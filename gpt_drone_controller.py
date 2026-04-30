import cv2
import base64
import time
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

PHASE_DESCEND = "descend"
PHASE_FIND_MAGNET = "find_magnet"
PHASE_COLLECT = "collect"
PHASE_VERIFY = "verify"
PHASE_RETURN = "return"


class GPTDroneController:
    def __init__(self, tello, gpt_api_key=None):
        self.tello = tello
        self.gpt_api_key = gpt_api_key or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.is_running = False
        self.phase = PHASE_DESCEND
        self.client = OpenAI(api_key=self.gpt_api_key)

    def encode_frame(self, frame):
        _, buffer = cv2.imencode(".jpg", frame)
        return base64.b64encode(buffer).decode("utf-8")

    def ask_gpt(self, frame, prompt):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{self.encode_frame(frame)}"
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                max_tokens=150,
            )
            content = response.choices[0].message.content
            content = (
                content.strip()
                .removeprefix("```json")
                .removeprefix("```")
                .removesuffix("```")
                .strip()
            )
            return json.loads(content)
        except (json.JSONDecodeError, Exception) as e:
            print(f"[GPT] Error: {e}")
            return None

    def wait_for_frame(self):
        print("[GPT] Waiting for camera feed...")
        while True:
            frame = self.tello.read()
            if frame is not None and frame.size > 0:
                print("[GPT] Camera ready")
                return frame
            time.sleep(0.1)

    def get_frame(self):
        frame = self.tello.read()
        if frame is None or frame.size == 0:
            return None
        return frame

    def run_autonomous_task(self, duration_seconds=120):
        self.is_running = True
        self.phase = PHASE_DESCEND
        print("[GPT] API started")

        self.wait_for_frame()

        start_time = time.time()
        last_gpt_send = 0

        while self.is_running and (time.time() - start_time) < duration_seconds:
            frame = self.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue

            if time.time() - last_gpt_send < 1.5:
                time.sleep(0.03)
                continue

            last_gpt_send = time.time()

            if self.phase == PHASE_DESCEND:
                self._phase_descend(frame)
            elif self.phase == PHASE_FIND_MAGNET:
                self._phase_find_magnet(frame)
            elif self.phase == PHASE_COLLECT:
                self._phase_collect(frame)
            elif self.phase == PHASE_VERIFY:
                self._phase_verify(frame)
            elif self.phase == PHASE_RETURN:
                self._phase_return()
                break

        if self.is_running:
            print("[TASK] Time limit reached - landing")
            self.tello.land()

        self.is_running = False

    def _phase_descend(self, frame):
        result = self.ask_gpt(
            frame,
            (
                "You are controlling a DJI Tello drone descending to find a water bottle on the floor. "
                "Look at this frame and return ONLY a JSON object with two fields: "
                "sees_bottle (bool), explanation. "
                "Set sees_bottle to true ONLY if you clearly see a water bottle in the frame."
            ),
        )
        if not result:
            return
        if result.get("sees_bottle"):
            print("[GPT] Bottle found")
            self.phase = PHASE_FIND_MAGNET
        else:
            self.tello.send_command("down 30")

    def _phase_find_magnet(self, frame):
        result = self.ask_gpt(
            frame,
            (
                "You are controlling a DJI Tello drone hovering above a water bottle. "
                "Look at this frame and return ONLY a JSON object with two fields: "
                "sees_magnet (bool), explanation. "
                "You are looking for a small circular magnet on top of the water bottle cap. "
                "Set sees_magnet to true ONLY if you clearly see the magnet on top of the bottle cap."
            ),
        )
        if not result:
            return
        if result.get("sees_magnet"):
            print("[GPT] Magnet found")
            self.phase = PHASE_COLLECT
        else:
            self.tello.send_command("down 20")

    def _phase_collect(self, frame):
        print("[GPT] Collecting magnet - flying over bottle")
        self.tello.send_command("forward 20")
        time.sleep(3)
        self.tello.send_command("back 40")
        time.sleep(3)
        self.phase = PHASE_VERIFY

    def _phase_verify(self, frame):
        result = self.ask_gpt(
            frame,
            (
                "You are controlling a DJI Tello drone. You just attempted to collect a magnet from the top of a water bottle. "
                "Look at this frame. Is there still a magnet visible on top of the water bottle cap? "
                "Return ONLY a JSON object with two fields: magnet_still_on_bottle (bool), explanation."
            ),
        )
        if not result:
            return
        if not result.get("magnet_still_on_bottle", True):
            print("[GPT] Magnet collected - returning to land")
            self.phase = PHASE_RETURN
        else:
            print("[GPT] Magnet still on bottle - retrying collection")
            self.phase = PHASE_FIND_MAGNET

    def _phase_return(self):
        print("[GPT] Landing")
        self.tello.send_command("up 50")
        time.sleep(3)
        self.tello.land()
        self.is_running = False
