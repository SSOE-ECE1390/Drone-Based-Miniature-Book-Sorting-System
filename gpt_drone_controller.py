import cv2
import base64
import time
from io import BytesIO
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class GPTDroneController:
    """
    Controls drone using ChatGPT vision API to interpret video feed
    and execute tasks autonomously.
    """

    def __init__(self, tello, gpt_api_key=None):
        """
        Initialize GPT Drone Controller

        Args:
            tello: Tello drone object
            gpt_api_key: OpenAI API key for ChatGPT (if None, loads from .env)
        """
        self.tello = tello
        # Load from .env if not provided
        if gpt_api_key is None:
            gpt_api_key = os.getenv("OPENAI_API_KEY")
        self.gpt_api_key = gpt_api_key
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-vision-preview")
        self.is_running = False
        self.task = None
        self.last_response = None

        if not self.gpt_api_key:
            print("[GPT] WARNING: OPENAI_API_KEY not found in .env file")

    def encode_frame_to_base64(self, frame):
        """
        Encode video frame to base64 for API transmission

        Args:
            frame: numpy array from drone camera

        Returns:
            base64 encoded string
        """
        _, buffer = cv2.imencode(".jpg", frame)
        return base64.b64encode(buffer).decode("utf-8")

    def send_frame_to_gpt(self, frame, task_instruction):
        """
        Send current drone frame to ChatGPT with task instruction

        Args:
            frame: current drone video frame
            task_instruction: what the drone should do (e.g., "land on water bottle")

        Returns:
            dict with drone action and confidence
        """
        if self.gpt_api_key is None:
            print("[GPT] API key not configured")
            return None

        try:
            import openai

            openai.api_key = self.gpt_api_key

            # Encode frame
            frame_b64 = self.encode_frame_to_base64(frame)

            # Send to GPT with vision capability
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": f"data:image/jpeg;base64,{frame_b64}",
                            },
                            {
                                "type": "text",
                                "text": f"""You are controlling a DJI Tello drone. 
                                
Current task: {task_instruction}

Analyze the current video frame and provide the next action the drone should take.

Respond ONLY with a JSON object in this format:
{{
    "action": "move_forward|move_backward|move_left|move_right|move_up|move_down|land|takeoff|rotate_cw|rotate_ccw|hover",
    "distance_or_degrees": <number>,
    "confidence": <0.0-1.0>,
    "explanation": "<brief reason>"
}}

Be decisive. If you can see the target (water bottle/magnet), move toward it. If you can't see it, suggest movement.""",
                            },
                        ],
                    }
                ],
                max_tokens=100,
            )

            # Parse response
            response_text = response.choices[0].message.content
            print(f"[GPT] {response_text}")

            # Try to parse JSON
            action_data = json.loads(response_text)

            # Check if water bottle was spotted
            explanation = action_data.get("explanation", "").lower()
            if "water" in explanation or "bottle" in explanation:
                print("[GPT] *** WATER SPOTTED ***")
                self.last_response = action_data

            return action_data

        except json.JSONDecodeError:
            print("[GPT] Could not parse response as JSON")
            return None
        except Exception as e:
            print(f"[GPT] Error: {e}")
            return None

    def execute_action(self, action_data):
        """
        Execute drone action from GPT response

        Args:
            action_data: dict with action and parameters
        """
        if action_data is None:
            return

        action = action_data.get("action", "hover")
        param = action_data.get("distance_or_degrees", 0.1)

        if action == "move_forward":
            self.tello.move_forward(param)
        elif action == "move_backward":
            self.tello.move_backward(param)
        elif action == "move_left":
            self.tello.move_left(param)
        elif action == "move_right":
            self.tello.move_right(param)
        elif action == "move_up":
            self.tello.move_up(param)
        elif action == "move_down":
            self.tello.move_down(param)
        elif action == "land":
            print("[DRONE] *** LANDING NOW ***")
            self.tello.land()
            self.is_running = False
        elif action == "takeoff":
            self.tello.takeoff()
        elif action == "rotate_cw":
            self.tello.rotate_cw(param)
        elif action == "rotate_ccw":
            self.tello.rotate_ccw(param)
        elif action == "hover":
            time.sleep(0.5)

    def run_autonomous_task(self, task_instruction, duration_seconds=30):
        """
        Run autonomous task for specified duration

        Args:
            task_instruction: what drone should do
            duration_seconds: how long to attempt the task
        """
        self.is_running = True
        self.task = task_instruction
        start_time = time.time()

        print(f"[TASK] Starting: {task_instruction}")
        print(f"[TASK] Duration: {duration_seconds}s")

        last_gpt_send = time.time()
        while self.is_running and (time.time() - start_time) < duration_seconds:
            # Get current frame from drone
            frame = self.tello.read()

            if frame is None or frame.size == 0:
                time.sleep(0.1)
                continue

            # Only send 1 frame per second to ChatGPT (not every frame)
            current_time = time.time()
            if current_time - last_gpt_send >= 1.0:
                # Send to GPT for analysis
                action_data = self.send_frame_to_gpt(frame, task_instruction)

                # Execute action
                if action_data:
                    self.execute_action(action_data)

                last_gpt_send = current_time

            # Display video at normal rate
            time.sleep(0.03)

        print(f"[TASK] Completed: {task_instruction}")
        self.is_running = False
