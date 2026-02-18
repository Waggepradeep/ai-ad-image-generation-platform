import os
import time
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from types import SimpleNamespace

import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit_drawable_canvas import st_canvas

from services import (
    add_shadow,
    create_packshot,
    enhance_prompt,
    generate_hd_image,
    generative_fill,
    lifestyle_shot_by_image,
    lifestyle_shot_by_text,
)
from ui import (
    render_erase_tab,
    render_fill_tab,
    render_generate_tab,
    render_lifestyle_tab,
)
from utils import extract_result_urls

# Configure Streamlit page
st.set_page_config(
    page_title="AdForge Studio",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Load environment variables
load_dotenv()

SOURCE_TO_FEATURE = {
    "Generate Image": "generate",
    "Lifestyle Shot": "lifestyle",
    "Generative Fill": "fill",
    "Erase Elements": "erase",
    "Create Packshot": "packshot",
    "Add Shadow": "shadow",
}

RECOMMENDED_VERSIONS = {
    "streamlit": "1.32.0",
    "streamlit-drawable-canvas": "0.9.3",
}


def initialize_session_state():
    """Initialize session state variables."""
    if "api_key" not in st.session_state:
        st.session_state.api_key = os.getenv("BRIA_API_KEY")
    if "generated_images" not in st.session_state:
        st.session_state.generated_images = []
    if "current_image" not in st.session_state:
        st.session_state.current_image = None
    if "pending_urls" not in st.session_state:
        st.session_state.pending_urls = []
    if "pending_source" not in st.session_state:
        st.session_state.pending_source = None
    if "edited_image" not in st.session_state:
        st.session_state.edited_image = None
    if "result_source" not in st.session_state:
        st.session_state.result_source = None
    if "original_prompt" not in st.session_state:
        st.session_state.original_prompt = ""
    if "enhanced_prompt" not in st.session_state:
        st.session_state.enhanced_prompt = None

    # Standardized cross-feature image state
    if "active_image" not in st.session_state:
        st.session_state.active_image = None
    if "active_source" not in st.session_state:
        st.session_state.active_source = None
    if "feature_images" not in st.session_state:
        st.session_state.feature_images = {
            "generate": None,
            "lifestyle": None,
            "fill": None,
            "erase": None,
            "packshot": None,
            "shadow": None,
        }
    if "generation_status" not in st.session_state:
        st.session_state.generation_status = {
            "state": "Idle",
            "message": "No active requests.",
            "updated_at": None,
        }
    if "last_action_ts" not in st.session_state:
        st.session_state.last_action_ts = {}
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False


def debug_log(event, **fields):
    """Log structured debug records when debug mode is enabled."""
    if not st.session_state.get("debug_mode"):
        return
    payload = {
        "ts": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "event": event,
        **fields,
    }
    st.sidebar.code(str(payload))


def set_generation_status(state, message):
    st.session_state.generation_status = {
        "state": state,
        "message": message,
        "updated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


def can_submit_action(action_key, cooldown_seconds=1.5):
    """Prevent duplicate rapid submissions for the same action."""
    now = time.time()
    last_ts = st.session_state.last_action_ts.get(action_key, 0.0)
    if now - last_ts < cooldown_seconds:
        return False
    st.session_state.last_action_ts[action_key] = now
    return True


def get_installed_version(pkg):
    try:
        return version(pkg)
    except PackageNotFoundError:
        return None


def check_runtime_versions():
    mismatches = []
    for pkg, expected in RECOMMENDED_VERSIONS.items():
        installed = get_installed_version(pkg)
        if installed is None:
            mismatches.append(f"{pkg} is not installed")
        elif installed != expected:
            mismatches.append(f"{pkg}={installed} (recommended {expected})")
    return mismatches


def api_error(exc: Exception, operation: str = "Request"):
    """Render consistent API error messaging across tabs."""
    msg = str(exc)
    set_generation_status("Failed", f"{operation} failed")
    debug_log("api_error", operation=operation, message=msg)
    st.error(f"{operation} failed: {msg}")

    if "status=422" in msg or " 422" in msg:
        st.warning(
            "The API rejected the request (422). Try a simpler/safer prompt, "
            "a smaller mask, or different generation settings."
        )
    elif "status=429" in msg or " 429" in msg:
        st.warning("Rate limit hit (429). Wait a moment and retry.")
    elif "status=5" in msg or " 500" in msg or " 502" in msg or " 503" in msg:
        st.warning("Image service is temporarily unavailable. Retry in a few seconds.")
    elif "network error" in msg.lower() or "timed out" in msg.lower():
        st.warning("Network timeout/connection issue. Please retry.")


def sync_active_image_state():
    """Keep unified active image + per-feature image state in sync."""
    image_url = st.session_state.get("edited_image")
    source = st.session_state.get("result_source")
    if not image_url:
        return

    st.session_state.active_image = image_url
    st.session_state.active_source = source

    feature_key = SOURCE_TO_FEATURE.get(source)
    if feature_key:
        st.session_state.feature_images[feature_key] = image_url
    set_generation_status("Ready", f"Latest image source: {source or 'Unknown'}")


def download_image(url):
    """Download image from URL and return as bytes."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        api_error(e, "Download image")
        return None


def check_generated_images():
    """Check if pending images are ready and update the display."""
    if st.session_state.pending_urls:
        ready_images = []
        still_pending = []

        for url in st.session_state.pending_urls:
            try:
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    ready_images.append(url)
                else:
                    still_pending.append(url)
            except Exception:
                still_pending.append(url)

        st.session_state.pending_urls = still_pending

        if ready_images:
            st.session_state.edited_image = ready_images[0]
            st.session_state.result_source = st.session_state.get("pending_source")
            if len(ready_images) > 1:
                st.session_state.generated_images = ready_images
            debug_log("pending_images_ready", count=len(ready_images), source=st.session_state.result_source)
            sync_active_image_state()
            return True

    return False


def auto_check_images(status_container):
    """Automatically check for image completion a few times."""
    max_attempts = 3
    attempt = 0
    while attempt < max_attempts and st.session_state.pending_urls:
        time.sleep(2)
        if check_generated_images():
            status_container.success("✨ Image ready!")
            return True
        attempt += 1
    return False


def safe_st_canvas(**kwargs):
    """Create drawable canvas with compatibility handling for Streamlit versions."""
    try:
        return st_canvas(**kwargs)
    except AttributeError as e:
        if "image_to_url" in str(e):
            st.error(
                "Drawable canvas is incompatible with your Streamlit version. "
                "Use streamlit==1.32.0 and streamlit-drawable-canvas==0.9.3."
            )
            return SimpleNamespace(image_data=None)
        raise


def render_generated_gallery(section_key):
    """Render generated image variations and allow selecting a primary image."""
    urls = st.session_state.get("generated_images", [])
    if not urls:
        return

    st.markdown("### Generated Variations")
    captions = [f"Variation {i + 1}" for i in range(len(urls))]
    st.image(urls, caption=captions, use_column_width=True)

    selected_index = st.selectbox(
        "Choose primary image",
        options=list(range(len(urls))),
        format_func=lambda i: f"Variation {i + 1}",
        key=f"{section_key}_primary_selection",
    )

    if st.button("Set as primary image", key=f"{section_key}_set_primary"):
        st.session_state.edited_image = urls[selected_index]
        sync_active_image_state()
        st.rerun()


def main():
    st.title("AdForge Studio")
    initialize_session_state()

    with st.sidebar:
        st.header("Settings")
        api_key_input = st.text_input(
            "Enter your API key:",
            value="",
            type="password",
            placeholder="Paste Bria API key (optional if set in .env)",
        )
        if api_key_input:
            st.session_state.api_key = api_key_input
        st.caption("API key is masked and never rendered in logs.")

        st.session_state.debug_mode = st.checkbox(
            "Debug mode",
            value=st.session_state.debug_mode,
            help="Shows structured event logs in sidebar.",
        )

        status = st.session_state.generation_status
        st.markdown("**Generation Status**")
        st.info(f"{status['state']}: {status['message']}")
        if status.get("updated_at"):
            st.caption(f"Updated: {status['updated_at']}")

        mismatches = check_runtime_versions()
        if mismatches:
            st.warning("Version compatibility notice:\n\n- " + "\n- ".join(mismatches))

    tabs = st.tabs([
        "🎨 Generate Image",
        "🖼️ Lifestyle Shot",
        "🎨 Generative Fill",
        "🎨 Erase Elements",
    ])

    common_deps = {
        "download_image": download_image,
        "extract_result_urls": extract_result_urls,
        "check_generated_images": check_generated_images,
        "auto_check_images": auto_check_images,
        "safe_st_canvas": safe_st_canvas,
        "render_generated_gallery": render_generated_gallery,
        "api_error": api_error,
        "debug_log": debug_log,
        "set_generation_status": set_generation_status,
        "can_submit_action": can_submit_action,
    }

    render_generate_tab(
        tabs[0],
        {
            **common_deps,
            "enhance_prompt": enhance_prompt,
            "generate_hd_image": generate_hd_image,
        },
    )
    sync_active_image_state()

    render_lifestyle_tab(
        tabs[1],
        {
            **common_deps,
            "create_packshot": create_packshot,
            "add_shadow": add_shadow,
            "lifestyle_shot_by_text": lifestyle_shot_by_text,
            "lifestyle_shot_by_image": lifestyle_shot_by_image,
        },
    )
    sync_active_image_state()

    render_fill_tab(
        tabs[2],
        {
            **common_deps,
            "generative_fill": generative_fill,
        },
    )
    sync_active_image_state()

    render_erase_tab(
        tabs[3],
        {
            **common_deps,
            "generative_fill": generative_fill,
        },
    )
    sync_active_image_state()


if __name__ == "__main__":
    main()
