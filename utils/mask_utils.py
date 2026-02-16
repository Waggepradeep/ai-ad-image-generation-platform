import io

import numpy as np
from PIL import Image


def prepare_binary_mask_bytes(image_data, target_size, threshold=25, invert=False):
    """
    Convert RGBA canvas image_data to a strict binary mask PNG.
    White (255) = masked area, Black (0) = keep area.
    """
    mask_img = Image.fromarray(image_data.astype("uint8"), mode="RGBA").convert("L")
    mask_img = mask_img.resize(target_size)
    arr = np.array(mask_img, dtype=np.uint8)
    binary = (arr > int(threshold)).astype(np.uint8) * 255
    if invert:
        binary = 255 - binary
    out_img = Image.fromarray(binary, mode="L")
    out = io.BytesIO()
    out_img.save(out, format="PNG")
    return out.getvalue(), out_img
