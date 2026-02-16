import numpy as np
import streamlit as st
from PIL import Image

from utils import prepare_binary_mask_bytes


def render(tab, deps):
    safe_st_canvas = deps['safe_st_canvas']
    generative_fill = deps['generative_fill']
    extract_result_urls = deps['extract_result_urls']
    download_image = deps['download_image']
    auto_check_images = deps['auto_check_images']
    check_generated_images = deps['check_generated_images']
    api_error = deps['api_error']
    debug_log = deps['debug_log']
    set_generation_status = deps['set_generation_status']
    can_submit_action = deps['can_submit_action']

    with tab:
        st.header("🎨 Generative Fill")
        st.markdown("Draw a mask on the image and describe what you want to generate in that area.")

        uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"], key="fill_upload")
        if uploaded_file:
            col1, col2 = st.columns(2)

            with col1:
                st.image(uploaded_file, caption="Original Image", use_column_width=True)

                img = Image.open(uploaded_file)
                img_width, img_height = img.size

                aspect_ratio = img_height / img_width
                canvas_width = min(img_width, 800)
                canvas_height = int(canvas_width * aspect_ratio)

                img = img.resize((canvas_width, canvas_height))

                if img.mode != "RGB":
                    img = img.convert("RGB")

                img_array = np.array(img).astype(np.uint8)

                stroke_width = st.slider("Brush width", 1, 50, 20)
                stroke_color = st.color_picker("Brush color", "#fff")

                canvas_result = safe_st_canvas(
                    fill_color="rgba(255, 255, 255, 0.0)",
                    stroke_width=stroke_width,
                    stroke_color=stroke_color,
                    drawing_mode="freedraw",
                    background_color="",
                    background_image=img if img_array.shape[-1] == 3 else None,
                    height=canvas_height,
                    width=canvas_width,
                    key="canvas",
                )

                st.subheader("Mask Options")
                mask_threshold = st.slider("Mask threshold", 0, 255, 25, key="fill_mask_threshold")
                invert_mask = st.checkbox("Invert mask", value=False, key="fill_invert_mask")
                show_mask_preview = st.checkbox("Show mask preview", value=True, key="fill_show_mask")

                st.subheader("Generation Options")
                prompt = st.text_area("Describe what to generate in the masked area")
                negative_prompt = st.text_area("Describe what to avoid (optional)")

                col_a, col_b = st.columns(2)
                with col_a:
                    num_results = st.slider("Number of variations", 1, 4, 1)
                    sync_mode = st.checkbox(
                        "Synchronous Mode",
                        True,
                        help="Wait for results instead of getting URLs immediately",
                        key="gen_fill_sync_mode",
                    )

                with col_b:
                    seed = st.number_input(
                        "Seed (optional)",
                        min_value=0,
                        value=0,
                        help="Use same seed to reproduce results",
                    )
                    content_moderation = st.checkbox(
                        "Enable Content Moderation",
                        False,
                        key="gen_fill_content_mod",
                    )

                if show_mask_preview and canvas_result.image_data is not None:
                    _, preview_mask = prepare_binary_mask_bytes(
                        canvas_result.image_data,
                        target_size=(img_width, img_height),
                        threshold=mask_threshold,
                        invert=invert_mask,
                    )
                    st.image(preview_mask, caption="Mask Preview (white = editable area)", use_column_width=True)

                if st.button("🎨 Generate", type="primary"):
                    if not prompt:
                        st.error("Please enter a prompt describing what to generate.")
                        return
                    if canvas_result.image_data is None:
                        st.error("Please draw a mask on the image first.")
                        return
                    if not can_submit_action("generative_fill"):
                        st.warning("Please wait a moment before submitting again.")
                        return

                    mask_bytes, _ = prepare_binary_mask_bytes(
                        canvas_result.image_data,
                        target_size=(img_width, img_height),
                        threshold=mask_threshold,
                        invert=invert_mask,
                    )
                    image_bytes = uploaded_file.getvalue()

                    set_generation_status("Generating", "Running generative fill...")
                    with st.spinner("Generating..."):
                        try:
                            result = generative_fill(
                                st.session_state.api_key,
                                image_bytes,
                                mask_bytes,
                                prompt,
                                negative_prompt=negative_prompt if negative_prompt else None,
                                num_results=num_results,
                                sync=sync_mode,
                                seed=seed if seed != 0 else None,
                                content_moderation=content_moderation,
                            )

                            if result:
                                urls = extract_result_urls(result, limit=num_results)
                                if sync_mode:
                                    if urls:
                                        st.session_state.edited_image = urls[0]
                                        st.session_state.generated_images = urls
                                        st.session_state.result_source = "Generative Fill"
                                        debug_log("image_generated", tab="Generative Fill", count=len(urls))
                                        st.success("Generation complete!")
                                    else:
                                        st.error("Generation completed but no image URL was returned.")
                                else:
                                    if urls:
                                        st.session_state.pending_urls = urls
                                        st.session_state.pending_source = "Generative Fill"

                                        status_container = st.empty()
                                        refresh_container = st.empty()

                                        status_container.info(
                                            f"Generation started! Waiting for {len(st.session_state.pending_urls)} image{'s' if len(st.session_state.pending_urls) > 1 else ''}..."
                                        )

                                        if auto_check_images(status_container):
                                            st.rerun()

                                        if refresh_container.button("Check for Generated Images"):
                                            if check_generated_images():
                                                status_container.success("Images ready!")
                                                st.rerun()
                                            else:
                                                status_container.warning("Still generating... Please check again in a moment.")
                        except Exception as e:
                            api_error(e, "Generative fill")

            with col2:
                if st.session_state.edited_image:
                    src = st.session_state.get("result_source")
                    if src and src != "Generative Fill":
                        st.info(f"Current image was generated in: {src}")
                    st.image(st.session_state.edited_image, caption="Generated Result", use_column_width=True)
                    image_data = download_image(st.session_state.edited_image)
                    if image_data:
                        st.download_button(
                            "Download Result",
                            image_data,
                            "generated_fill.png",
                            "image/png",
                        )
                elif st.session_state.pending_urls:
                    st.info("Generation in progress. Click the refresh button above to check status.")