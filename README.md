# AdSnap Studio

AdSnap Studio is a Streamlit app for generating and editing ad images using Bria AI APIs.

## What It Does

- Generate images from text prompts (HD text-to-image)
- Enhance prompts before generation
- Lifestyle Shot workflows:
  - Create Packshot
  - Add Shadow
  - Lifestyle shot by text prompt
  - Lifestyle shot by reference image
- Generative Fill using a user-drawn mask
- Erase Elements using a user-drawn mask and fill prompt
- Download generated outputs

## Current Project Structure

- `app.py`: app bootstrap, shared session state, status handling, dependency wiring
- `ui/generate_tab.py`: Generate Image tab
- `ui/lifestyle_tab.py`: Lifestyle Shot tab
- `ui/fill_tab.py`: Generative Fill tab
- `ui/erase_tab.py`: Erase Elements tab
- `services/`: API service wrappers
- `utils/result_utils.py`: response URL extraction helper
- `utils/mask_utils.py`: binary mask preparation helper
- `tests/test_result_utils.py`: parser tests
- `app.py.bak`: old monolithic backup (optional, not used at runtime)

## Requirements

Pinned runtime versions are recommended for compatibility:

- `streamlit==1.32.0`
- `streamlit-drawable-canvas==0.9.3`
- `requests==2.31.0`
- `python-dotenv==1.0.1`
- `Pillow==10.2.0`

Install:

```bash
pip install -r requirements.txt
```

## Environment

Create `.env` in project root:

```bash
BRIA_API_KEY=your_api_key_here
```

You can also enter the key in the sidebar at runtime. The key input is masked.

## Run

Use Streamlit runner (important):

```bash
streamlit run app.py
```

Do not run with:

```bash
python app.py
```

Running with `python app.py` causes Streamlit session/context warnings and broken behavior.

## Important Fixes Implemented

- Refactored `app.py` into modular tab files under `ui/`
- Added standardized cross-feature image state:
  - `active_image`, `active_source`, `feature_images`
- Added centralized API error handling (`422`, `429`, `5xx`, network)
- Fixed Erase Elements behavior to use drawn mask area (not foreground-removal endpoint)
- Added consistent source messaging across tabs:
  - `Current image was generated in: <source>`
- Added mask quality improvements:
  - binary mask conversion
  - configurable threshold
  - invert mask
  - mask preview
- Added basic request throttling to reduce accidental duplicate submits
- Added cached image downloads for performance
- Added debug mode with structured sidebar logs
- Added runtime version compatibility warning in sidebar
- Added tests for result URL extraction helper

## Status + Debug UX

Sidebar includes:

- Generation status (`Idle`, `Generating`, `Ready`, `Failed`)
- Debug mode toggle (structured event logs)
- Version compatibility warning if installed packages differ from recommended versions

## Testing

Run tests:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## Known Notes

- `app.py.bak` is an older backup and may be much larger than current `app.py`.
- Current app logic is modular; runtime uses `app.py` + `ui/*` modules.
- Some older warnings in terminal/UI are caused by version mismatches or deprecated args in old branches; use pinned versions above.

## Next Suggested Work (High Value)

- Refactor `ui/lifestyle_tab.py` into smaller helpers (largest remaining module)
- Add integration tests with mocked API responses
- Add lint/format/type checks in CI (`ruff`, `black`, optional `mypy`)

## License

This project is licensed under the MIT License.