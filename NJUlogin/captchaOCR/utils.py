import base64
import io
from PIL import Image


def base64_to_image(img_base64):
    img_data = base64.b64decode(img_base64)
    return Image.open(io.BytesIO(img_data))


def image_to_base64(single_image_path):
    with open(single_image_path, "rb") as fp:
        img_base64 = base64.b64encode(fp.read())
        return img_base64.decode()
