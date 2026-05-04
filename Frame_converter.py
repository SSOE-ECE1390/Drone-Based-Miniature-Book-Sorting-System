import base64
import os

import cv2
from openai import OpenAI

VALID_SYMBOLS = ["I", "+", "X", "-", "[]", "O"]

_PROMPT = (
    "The image shows a shelf with exactly 6 books in a row. "
    "Each book has one printed symbol on its spine, drawn from this set: "
    f"{VALID_SYMBOLS}. "
    "Return the symbols you see, left to right, as a comma-separated list "
    "with no extra text, no spaces, no quotes. "
    "Example output: I,+,X,-,[],O"
)


class FrameToSymbols:
    def __init__(self, api_key=None, model="gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.model = model
        self.timeout = float(os.environ.get("FRAME_TO_SYMBOLS_TIMEOUT", "10"))
        self.max_image_side = int(os.environ.get("FRAME_TO_SYMBOLS_MAX_SIDE", "640"))

    def detect(self, frame):
        b64 = self._encode_jpeg(frame)
        if b64 is None:
            return None

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": _PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64}",
                                    "detail": "high",
                                },
                            },
                        ],
                    }
                ],
                max_tokens=50,
                timeout=self.timeout,
            )
        except Exception as e:
            print(f"[FRAME→SYMBOLS] API error: {e}")
            return None

        text = resp.choices[0].message.content.strip()
        print(f"[GPT → SYSTEM] {text}")
        return self._parse(text)

    def _encode_jpeg(self, frame):
        try:
            bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            height, width = bgr.shape[:2]
            longest_side = max(height, width)
            if longest_side > self.max_image_side:
                scale = self.max_image_side / float(longest_side)
                bgr = cv2.resize(
                    bgr,
                    (int(width * scale), int(height * scale)),
                    interpolation=cv2.INTER_AREA,
                )
            ok, buf = cv2.imencode(
                ".jpg",
                bgr,
                [int(cv2.IMWRITE_JPEG_QUALITY), 70],
            )
            if not ok:
                return None
            return base64.b64encode(buf.tobytes()).decode("utf-8")
        except Exception as e:
            print(f"[FRAME→SYMBOLS] encode error: {e}")
            return None

    def _parse(self, text):
        parts = [p.strip() for p in text.split(",")]
        if len(parts) != 6:
            return None
        for p in parts:
            if p not in VALID_SYMBOLS:
                return None
        for sym in VALID_SYMBOLS:
            if parts.count(sym) > 1:
                return None
        return parts
