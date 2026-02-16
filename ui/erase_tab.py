import streamlit as st
from PIL import Image

from utils import prepare_binary_mask_bytes


def render(tab, deps):
    safe_st_canvas = deps['safe_st_canvas']
    generative_fill = deps['generative_fill']
    extract_result_urls = deps['extract_result_urls']
    download_image = deps['download_image']
    api_error = deps['api_error']
    debug_log = deps['debug_log']
    set_generation_status = deps['set_generation_status']
    can_submit_action = deps['can_submit_action']

    with tab:
        st.header("🎨 Erase Elements")
        st.markdown("Upload an image and select the area you want to erase.")

        uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"], key="erase_upload")
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

                stroke_width = st.slider("Brush width", 1, 50, 20, key="erase_brush_width")
                stroke_color = st.color_picker("Brush color", "#fff", key="erase_brush_color")

                canvas_result = safe_st_canvas(
                    fill_color="rgba(255, 255, 255, 0.0)",
                    stroke_width=stroke_width,
                    stroke_color=stroke_color,
                    background_color="",
                    background_image=img,
                    drawing_mode="freedraw",
                    height=canvas_height,
                    width=canvas_width,
                    key="erase_canvas",
                )

                st.subheader("Erase Options")
                content_moderation = st.checkbox("Enable Content Moderation", False, key="erase_content_mod")
                erase_prompt = st.text_input(
                    "Fill prompt (optional)",
                    value="remove selected object and fill with natural background",
                    key="erase_fill_prompt",
                )
                mask_threshold = st.slider("Mask threshold", 0, 255, 25, key="erase_mask_threshold")
                invert_mask = st.checkbox("Invert mask", value=False, key="erase_invert_mask")
                show_mask_preview = st.checkbox("Show mask preview", value=True, key="erase_show_mask")

                if show_mask_preview and canvas_result.image_data is not None:
                    _, preview_mask = prepare_binary_mask_bytes(
                        canvas_result.image_data,
                        target_size=(img_width, img_height),
                        threshold=mask_threshold,
                        invert=invert_mask,
                    )
                    st.image(preview_mask, caption="Mask Preview (white = erase area)", use_column_width=True)

                if st.button("🎨 Erase Selected Area", key="erase_btn"):
                    if canvas_result.image_data is None:
                        st.warning("Please draw on the image to select the area to erase.")
                        return
                    if not can_submit_action("erase_elements"):
                        st.warning("Please wait a moment before submitting again.")
                        return

                    mask_bytes, _ = prepare_binary_mask_bytes(
                        canvas_result.image_data,
                        target_size=(img_width, img_height),
                        threshold=mask_threshold,
                        invert=invert_mask,
                    )
                    image_bytes = uploaded_file.getvalue()

                    set_generation_status("Generating", "Erasing selected area...")
                    with st.spinner("Erasing selected area..."):
                        try:
                            result = generative_fill(
                                st.session_state.api_key,
                                image_data=image_bytes,
                                mask_data=mask_bytes,
                                prompt=erase_prompt.strip() if erase_prompt and erase_prompt.strip() else "remove selected object and fill with natural background",
                                num_results=1,
                                sync=True,
                                content_moderation=content_moderation,
                            )

                            if result:
                                urls = extract_result_urls(result, limit=1)
                                if urls:
                                    st.session_state.edited_image = urls[0]
                                    st.session_state.generated_images = urls
                                    st.session_state.result_source = "Erase Elements"
                                    debug_log("image_generated", tab="Erase Elements", count=1)
                                    st.success("Area erased successfully!")
                                else:
                                    st.error("No result URL in the API response. Please try again.")
                        except Exception as e:
                            api_error(e, "Erase selected area")

            with col2:
                if st.session_state.edited_image:
                    src = st.session_state.get("result_source")
                    if src and src != "Erase Elements":
                        st.info(f"Current image was generated in: {src}")
                    st.image(st.session_state.edited_image, caption="Result", use_column_width=True)
                    image_data = download_image(st.session_state.edited_image)
                    if image_data:
                        st.download_button(
                            "Download Result",
                            image_data,
                            "erased_image.png",
                            "image/png",
                            key="erase_download",
                        )