import streamlit as st


def render(tab, deps):
    enhance_prompt = deps['enhance_prompt']
    generate_hd_image = deps['generate_hd_image']
    extract_result_urls = deps['extract_result_urls']
    download_image = deps['download_image']
    api_error = deps['api_error']
    debug_log = deps['debug_log']
    set_generation_status = deps['set_generation_status']
    can_submit_action = deps['can_submit_action']

    with tab:
        st.header("🎨 Generate Images")

        col1, col2 = st.columns([2, 1])
        with col1:
            prompt = st.text_area("Enter your prompt", value="", height=100, key="prompt_input")
            negative_prompt = st.text_area(
                "Negative prompt (optional)",
                value="",
                height=80,
                key="prompt_negative_input",
            )

            if "original_prompt" not in st.session_state:
                st.session_state.original_prompt = prompt
            elif prompt != st.session_state.original_prompt:
                st.session_state.original_prompt = prompt
                st.session_state.enhanced_prompt = None

            if st.session_state.get("enhanced_prompt"):
                st.markdown("**Enhanced Prompt:**")
                st.markdown(f"*{st.session_state.enhanced_prompt}*")

            if st.button("✨ Enhance Prompt", key="enhance_button"):
                if not prompt:
                    st.warning("Please enter a prompt to enhance.")
                else:
                    if not can_submit_action("enhance_prompt"):
                        st.warning("Please wait a moment before trying again.")
                        return
                    set_generation_status("Generating", "Enhancing prompt...")
                    with st.spinner("Enhancing prompt..."):
                        try:
                            result = enhance_prompt(st.session_state.api_key, prompt)
                            if result:
                                st.session_state.enhanced_prompt = result
                                debug_log("prompt_enhanced")
                                st.success("Prompt enhanced!")
                                st.rerun()
                        except Exception as e:
                            api_error(e, "Enhance prompt")

        with col2:
            num_images = st.slider("Number of images", 1, 4, 1)
            aspect_ratio = st.selectbox("Aspect ratio", ["1:1", "16:9", "9:16", "4:3", "3:4"])
            enhance_img = st.checkbox("Enhance image quality", value=True)

            st.subheader("Style Options")
            style = st.selectbox(
                "Image Style",
                [
                    "Realistic",
                    "Artistic",
                    "Cartoon",
                    "Sketch",
                    "Watercolor",
                    "Oil Painting",
                    "Digital Art",
                ],
            )

            if style and style != "Realistic":
                prompt = f"{prompt}, in {style.lower()} style"

        if st.button("🎨 Generate Images", type="primary"):
            if not st.session_state.api_key:
                st.error("Please enter your API key in the sidebar.")
                return
            if not can_submit_action("generate_image"):
                st.warning("Please wait a moment before submitting again.")
                return

            set_generation_status("Generating", "Generating images...")
            with st.spinner("Generating your masterpiece..."):
                try:
                    result = generate_hd_image(
                        prompt=st.session_state.enhanced_prompt or prompt,
                        api_key=st.session_state.api_key,
                        num_results=num_images,
                        aspect_ratio=aspect_ratio,
                        negative_prompt=negative_prompt,
                        sync=True,
                        enhance_image=enhance_img,
                        medium="art" if style != "Realistic" else "photography",
                        prompt_enhancement=False,
                        content_moderation=True,
                    )

                    if result:
                        urls = extract_result_urls(result, limit=num_images)
                        if urls:
                            st.session_state.edited_image = urls[0]
                            st.session_state.generated_images = urls
                            st.session_state.result_source = "Generate Image"
                            debug_log("image_generated", tab="Generate Image", count=len(urls))
                            st.success("Image generated successfully!")
                        else:
                            st.error("No valid image URLs found in the API response.")
                except Exception as e:
                    api_error(e, "Generate image")

        if st.session_state.edited_image:
            src = st.session_state.get("result_source")
            if src and src != "Generate Image":
                st.info(f"Current image was generated in: {src}")
            st.image(st.session_state.edited_image, caption="Generated Image", use_column_width=True)
            image_data = download_image(st.session_state.edited_image)
            if image_data:
                st.download_button(
                    "Download Generated Image",
                    image_data,
                    "generated_image.png",
                    "image/png",
                    key="generate_download",
                )
