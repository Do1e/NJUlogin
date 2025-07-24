from typing import Union, Optional
import io
import json
import os.path as osp
import pathlib
import numpy as np
import onnxruntime
from PIL import Image

from .utils import base64_to_image


class CaptchaOCR:
    def __init__(
        self,
        gpu_id: int = -1,
    ):
        import_onnx_path = osp.join(osp.dirname(__file__), 'nju_captcha.onnx')
        self.charset = ['1', '2', '3', '4', '5', '6', '7', '8', 'a', 'b', 'c', 'd', 'e', 'f', 'h', 'k', 'n', 'p', 'q', 'x', 'y', 'z']
        self.resize = (176, 64)
        if gpu_id >= 0:
            providers = [
                (
                    "CUDAExecutionProvider",
                    {
                        "device_id": gpu_id,
                        "arena_extend_strategy": "kNextPowerOfTwo",
                        "cuda_mem_limit": 2 * 1024 * 1024 * 1024,
                        "cudnn_conv_algo_search": "EXHAUSTIVE",
                        "do_copy_in_default_stream": True,
                    },
                ),
            ]
        else:
            providers = ["CPUExecutionProvider"]
        self.ort_session = onnxruntime.InferenceSession(
            import_onnx_path, providers=providers
        )

    def get_text(self, img: Union[bytes, str, pathlib.PurePath, Image.Image]):
        if not isinstance(img, (bytes, str, pathlib.PurePath, Image.Image)):
            raise TypeError(
                "img must be bytes, str, pathlib.PurePath or PIL.Image.Image"
            )
        if isinstance(img, bytes):
            image = Image.open(io.BytesIO(img))
        elif isinstance(img, str):
            image = base64_to_image(img)
        elif isinstance(img, pathlib.PurePath):
            image = Image.open(img)
        elif isinstance(img, Image.Image):
            image = img.copy()
        else:
            raise TypeError(
                "img must be bytes, str, pathlib.PurePath or PIL.Image.Image"
            )

        image = image.resize(self.resize, Image.LANCZOS)
        image = image.convert("RGB")

        image = np.array(image, dtype=np.float32) / 255.0
        image = np.expand_dims(image, axis=0)
        image = (image - np.array([0.743, 0.7432, 0.7431], dtype=np.float32)) / np.array([0.1917, 0.1918, 0.1917], dtype=np.float32)
        image = np.transpose(image, (0, 3, 1, 2))
        image = image.astype(np.float32)
        ort_inputs = {'input': image}
        ort_outs = self.ort_session.run(None, ort_inputs)
        output = ort_outs[0]
        output = np.argmax(output, axis=2)
        output = output[0].tolist()
        text = ''.join([self.charset[i] for i in output])
        return text
