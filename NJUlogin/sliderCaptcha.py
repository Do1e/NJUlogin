from __future__ import annotations

import base64
import binascii
import json
import math
import random
import time
from dataclasses import dataclass
from typing import Callable, Protocol

import cv2
import numpy as np
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from .utils import urls


CANVAS_WIDTH = 280
BACKGROUND_DRAW_WIDTH = 278
MAX_SLIDER_DISTANCE = 240
DEFAULT_ATTEMPTS = 5
MIN_VERIFY_DELAY = 1.82
MAX_VERIFY_DELAY = 2.08

_PASSWORD_CHARS = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"
_MOVE_PROFILE = (
    0.0667,
    0.122,
    0.211,
    0.367,
    0.5,
    0.622,
    0.733,
    0.778,
    0.822,
    0.867,
    0.889,
    0.911,
    0.944,
    0.967,
    1.0,
)
_DEFAULT_RNG = random.SystemRandom()


class SliderCaptchaError(RuntimeError):
    """滑块验证码协议或图片格式异常。"""


class _HttpClient(Protocol):
    def get(self, url: str, **kwargs): ...

    def post(self, url: str, data: dict, **kwargs): ...


@dataclass(frozen=True)
class GapMatch:
    left: int
    center: tuple[int, int]
    confidence: float
    piece_bbox: tuple[int, int, int, int]
    background_width: int


def _decode_image(raw: bytes, flags: int, name: str) -> np.ndarray:
    image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), flags)
    if image is None:
        raise SliderCaptchaError(f"无法解码滑块{name}图片")
    return image


def _decode_base64(value: str, name: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise SliderCaptchaError(f"滑块响应缺少{name}")
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise SliderCaptchaError(f"滑块{name}不是有效的 Base64 数据") from exc


def locate_gap(background_bytes: bytes, piece_bytes: bytes) -> GapMatch:
    """用边缘模板匹配定位单一拼图缺口。"""
    background = _decode_image(background_bytes, cv2.IMREAD_COLOR, "背景")
    piece = _decode_image(piece_bytes, cv2.IMREAD_UNCHANGED, "拼图")
    if piece.ndim != 3 or piece.shape[2] != 4:
        raise SliderCaptchaError("滑块拼图图片缺少透明通道")

    visible = cv2.findNonZero(piece[:, :, 3])
    if visible is None:
        raise SliderCaptchaError("滑块拼图图片完全透明")
    piece_x, piece_y, piece_width, piece_height = cv2.boundingRect(visible)
    if piece_y + piece_height > background.shape[0]:
        raise SliderCaptchaError("滑块拼图尺寸超出背景图片")

    template = piece[
        piece_y : piece_y + piece_height,
        piece_x : piece_x + piece_width,
        :3,
    ]
    search_area = background[piece_y : piece_y + piece_height, :]
    if template.shape[0] > search_area.shape[0] or template.shape[1] > search_area.shape[1]:
        raise SliderCaptchaError("滑块拼图尺寸大于可搜索区域")

    template_edges = cv2.Canny(cv2.cvtColor(template, cv2.COLOR_BGR2GRAY), 50, 150)
    search_edges = cv2.Canny(cv2.cvtColor(search_area, cv2.COLOR_BGR2GRAY), 50, 150)
    scores = cv2.matchTemplate(search_edges, template_edges, cv2.TM_CCOEFF_NORMED)
    _, confidence, _, (left, relative_top) = cv2.minMaxLoc(scores)

    return GapMatch(
        left=int(left),
        center=(
            int(left + piece_width // 2),
            int(piece_y + relative_top + piece_height // 2),
        ),
        confidence=float(confidence),
        piece_bbox=(int(piece_x), int(piece_y), int(piece_width), int(piece_height)),
        background_width=int(background.shape[1]),
    )


def scale_move_length(left: int, background_width: int) -> int:
    """把原图缺口坐标换算为网页 280px 滑块坐标。"""
    if left < 0 or background_width <= 0:
        raise SliderCaptchaError("无效的滑块缺口坐标")
    # 前端把背景绘制到 278px canvas，并在滑块位置上补偿 2px 边框。
    move_length = math.floor(left * BACKGROUND_DRAW_WIDTH / background_width + 0.5) + 2
    if not 0 < move_length <= MAX_SLIDER_DISTANCE:
        raise SliderCaptchaError(f"滑块距离超出有效范围: {move_length}")
    return move_length


def generate_tracks(
    move_length: int, rng: random.Random | random.SystemRandom | None = None
) -> list[dict[str, int]]:
    """生成与网页事件采样规则一致的平滑拖动轨迹。"""
    if not 0 < move_length <= MAX_SLIDER_DISTANCE:
        raise SliderCaptchaError(f"滑块距离超出有效范围: {move_length}")
    rng = rng or _DEFAULT_RNG
    vertical = rng.choice((-1, 0, 1))
    tracks = [
        {"a": 0, "b": 0, "c": 0},
        {"a": 0, "b": rng.choice((-1, 0, 0, 1)), "c": rng.randint(28, 48)},
    ]
    last = 0

    for proportion in _MOVE_PROFILE:
        jitter = rng.uniform(-0.008, 0.008) if proportion < 1 else 0
        position = min(
            move_length,
            max(last, math.floor(move_length * (proportion + jitter) + 0.5)),
        )
        if position - last < 2 and proportion < 1:
            continue
        if rng.random() < 0.18:
            vertical = max(-2, min(2, vertical + rng.choice((-1, 0, 1))))
        tracks.append(
            {
                "a": int(position),
                "b": int(vertical),
                "c": rng.randint(21, 36),
            }
        )
        last = position

    if tracks[-1]["a"] != move_length:
        tracks.append({"a": move_length, "b": int(vertical), "c": rng.randint(45, 90)})
    else:
        tracks[-1]["c"] = rng.randint(45, 90)
    tracks.append({"a": move_length, "b": int(vertical), "c": rng.randint(220, 390)})
    return tracks


def encrypt_sign(
    payload: dict, key: bytes, rng: random.Random | random.SystemRandom | None = None
) -> str:
    """复现统一认证前端的 AES-CBC 签名格式。"""
    if len(key) != AES.block_size:
        raise SliderCaptchaError("滑块加密密钥长度不是 16 字节")
    rng = rng or _DEFAULT_RNG
    prefix = "".join(rng.choice(_PASSWORD_CHARS) for _ in range(64)).encode("utf-8")
    iv = "".join(rng.choice(_PASSWORD_CHARS) for _ in range(16)).encode("utf-8")
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return base64.b64encode(cipher.encrypt(pad(prefix + serialized, AES.block_size))).decode(
        "ascii"
    )


def _ajax_headers(referer: str) -> dict[str, str]:
    return {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": referer,
        "X-Requested-With": "XMLHttpRequest",
    }


def _solve_payload(payload: dict, rng) -> tuple[dict, bytes]:
    background_bytes = _decode_base64(payload.get("bigImage"), "背景图片")
    piece_bytes = _decode_base64(payload.get("smallImage"), "拼图图片")
    if len(piece_bytes) < AES.block_size:
        raise SliderCaptchaError("滑块拼图数据中缺少加密密钥")

    match = locate_gap(background_bytes, piece_bytes)
    move_length = scale_move_length(match.left, match.background_width)
    tracks = generate_tracks(move_length, rng)
    proof = {
        "canvasLength": CANVAS_WIDTH,
        "moveLength": move_length,
        "tracks": tracks,
    }
    return proof, piece_bytes[-AES.block_size :]


def verify_slider_captcha(
    client: _HttpClient,
    referer: str,
    *,
    attempts: int = DEFAULT_ATTEMPTS,
    rng: random.Random | random.SystemRandom | None = None,
    sleep: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
    min_delay: float = MIN_VERIFY_DELAY,
    max_delay: float = MAX_VERIFY_DELAY,
) -> bool:
    """打开、识别并验证滑块；验证失败时自动换一张图重试。"""
    if attempts <= 0:
        raise ValueError("attempts 必须大于 0")
    if min_delay < 0 or max_delay < min_delay:
        raise ValueError("无效的滑块等待时间范围")

    rng = rng or _DEFAULT_RNG
    headers = _ajax_headers(referer)
    for _ in range(attempts):
        to_response = client.get(urls.toSliderCaptcha, headers=headers)
        to_response.raise_for_status()

        opened_at = monotonic()
        open_response = client.get(
            urls.openSliderCaptcha,
            params={"_": int(time.time() * 1000)},
            headers=headers,
        )
        open_response.raise_for_status()
        try:
            challenge = open_response.json()
            if not isinstance(challenge, dict):
                raise SliderCaptchaError("滑块接口没有返回对象")
            proof, key = _solve_payload(challenge, rng)
            sign = encrypt_sign(proof, key, rng)
        except (ValueError, SliderCaptchaError):
            continue

        remaining = rng.uniform(min_delay, max_delay) - (monotonic() - opened_at)
        if remaining > 0:
            sleep(remaining)

        verify_response = client.post(
            urls.verifySliderCaptcha,
            data={"sign": sign},
            headers=headers,
        )
        verify_response.raise_for_status()
        try:
            error_code = verify_response.json().get("errorCode")
        except (ValueError, AttributeError):
            error_code = None
        if error_code == 1 or error_code == "1":
            return True
    return False
