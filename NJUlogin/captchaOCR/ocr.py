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
        use_import_onnx: bool = False,
        import_onnx_path: Optional[Union[str, pathlib.PurePath]] = None,
        charsets_path: Optional[Union[str, pathlib.PurePath]] = None,
    ):
        self.use_import_onnx = use_import_onnx
        if self.use_import_onnx:
            if import_onnx_path is None:
                raise ValueError(
                    "import_onnx_path must be specified when use_import_onnx is True"
                )
            if not isinstance(import_onnx_path, (str, pathlib.PurePath)):
                raise TypeError("import_onnx_path must be str or pathlib.PurePath")
            if charsets_path is None:
                raise ValueError(
                    "charsets_path must be specified when use_import_onnx is True"
                )
            if not isinstance(charsets_path, (str, pathlib.PurePath)):
                raise TypeError("charsets_path must be str or pathlib.PurePath")
            with open(charsets_path, "r", encoding="utf-8") as fp:
                info = json.load(fp)
            self.charset = info["charset"]
            self.word = info["word"]
            self.resize = info["image"]
            self.channel = info["channel"]
            if len(self.resize) != 2:
                raise ValueError("image must be a list of 2 elements")
            if self.channel not in (1, 3):
                raise ValueError("channel must be 1 or 3")
        else:
            from .charsets import charset

            import_onnx_path = osp.join(osp.dirname(__file__), "common.onnx")
            self.charset = charset
            self.word = False
            self.resize = (-1, 64)
            self.channel = 1
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

        if self.resize[0] == -1:
            if self.word:
                size = (int(self.resize[1]), int(self.resize[1]))
            else:
                size = (
                    int(image.size[0] * self.resize[1] / image.size[1]),
                    int(self.resize[1]),
                )
        else:
            size = (int(self.resize[0]), int(self.resize[1]))
        image = image.resize(size, Image.LANCZOS)
        if self.channel == 1:
            image = image.convert("L")
        else:
            image = image.convert("RGB")

        image = np.array(image, dtype=np.float32) / 255.0
        image = np.expand_dims(image, axis=0)
        if not self.use_import_onnx:
            image = (image - 0.5) / 0.5
        else:
            if self.channel == 1:
                image = (image - 0.456) / 0.224
            else:
                image = (image - np.array([0.485, 0.456, 0.406])) / np.array(
                    [0.229, 0.224, 0.225]
                )
                image = image[0]
                image = image.transpose((2, 0, 1))

        ort_inputs = {"input1": np.array([image]).astype(np.float32)}
        ort_outs = self.ort_session.run(None, ort_inputs)
        result = []
        last_item = 0
        if self.word:
            for item in ort_outs[1]:
                result.append(self.charset[item])
        else:
            for item in ort_outs[0][0]:
                if item == last_item:
                    continue
                if item != 0:
                    result.append(self.charset[item])
                last_item = item
        return "".join(result)
