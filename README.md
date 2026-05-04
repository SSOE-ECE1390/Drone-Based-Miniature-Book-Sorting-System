# Autonomous Drone-Based Miniature-Book-Sorting-System
**ECE 1895 Junior Design Fundamentals — University of Pittsburgh**
**Wunmi Salami**

---

## Table of Contents

1. [Introduction](#1-introduction)
   - [1.1 Project Overview](#11-project-overview)
   - [1.2 Motivation](#12-motivation)
   - [1.3 Project Goals](#13-project-goals)
2. [Design Overview](#2-design-overview)
   - [2.1 Original Concepts Considered](#21-original-concepts-considered)
   - [2.2 Final Design Description](#22-final-design-description)
   - [2.3 System Architecture](#23-system-architecture)
   - [2.4 How This Expands on Previous Work](#24-how-this-expands-on-previous-work)
   - [2.5 References and Schematics](#25-references-and-schematics)
3. [Preliminary Design Verification](#3-preliminary-design-verification)
   - [3.1 Drone Payload Verification](#31-drone-payload-verification)
   - [3.2 Shelf and Electromagnet Verification](#32-shelf-and-electromagnet-verification)
   - [3.3 GPT Vision API Verification](#33-gpt-vision-api-verification)
4. [Design Implementation](#4-design-implementation)
   - [4.1 System Overview](#41-system-overview)
   - [4.2 DJI Tello Drone Subsystem](#42-dji-tello-drone-subsystem)
   - [4.3 Smart Shelf Subsystem](#43-smart-shelf-subsystem)
   - [4.4 GPT Vision Controller](#44-gpt-vision-controller)
   - [4.5 Book Detection and Sorting Algorithm](#45-book-detection-and-sorting-algorithm)
   - [4.6 ESP32 Shelf Controller](#46-esp32-shelf-controller)
   - [4.7 3D Printed Books](#47-3d-printed-books)
   - [4.8 Inter-Subsystem Communication](#48-inter-subsystem-communication)
   - [4.9 Design Challenges](#49-design-challenges)
5. [Design Testing](#5-design-testing)
   - [5.1 Test Plan](#51-test-plan)
   - [5.2 Drone Takeoff and Landing Tests](#52-drone-takeoff-and-landing-tests)
   - [5.3 GPT Water Bottle Detection Test](#53-gpt-water-bottle-detection-test)
   - [5.4 Magnet Pickup Test](#54-magnet-pickup-test)
   - [5.5 Book Detection Test](#55-book-detection-test)
   - [5.6 Full System Integration Test](#56-full-system-integration-test)
   - [5.7 Unsuccessful Attempts and Fixes](#57-unsuccessful-attempts-and-fixes)
   - [5.8 Demonstration Videos](#58-demonstration-videos)
6. [Bill of Materials](#6-bill-of-materials)
   - [6.1 Hardware Components](#61-hardware-components)
7. [AI Usage Summary](#7-ai-usage-summary)
   - [7.1 Where AI Was Used](#71-where-ai-was-used)
   - [7.2 Example of AI Use](#72-example-of-ai-use)
8. [Summary, Conclusions and Future Work](#8-summary-conclusions-and-future-work)
   - [8.1 Project Summary](#81-project-summary)
   - [8.2 Conclusions](#82-conclusions)
   - [8.3 What I Would Do Differently](#83-what-i-would-do-differently)
   - [8.4 Future Work](#84-future-work)

---

## 1. Introduction

### 1.1 Project Overview

This project is an Autonomous Drone-Based Librarian System — a prototype that uses a DJI Tello drone to autonomously identify, pick up, and reorder miniature 3D-printed books on a smart electromagnetic shelf. The drone uses a GPT-4o vision model to interpret its camera feed in real time, identify books by shape markers printed on their spines, and execute pick-and-place operations using a magnetic attachment mechanism. The shelf is controlled by an ESP32-S3 microcontroller that activates individual electromagnets to hold books securely in their assigned slots.

### 1.2 Motivation

The idea came directly from real library work experience. Manual shelf reading — walking the stacks, checking that every book is in its correct position — is one of the most repetitive and error-prone tasks in library operations. A single misplaced book can go unnoticed for weeks. This project asks: what if a drone could do that autonomously? Not just scan, but physically correct the order. That question is what drove every design decision from component selection to software architecture.

### 1.3 Project Goals

- A DJI Tello drone takes off autonomously and navigates a shelf using its onboard camera and GPT-4o vision
- The drone identifies each book by its unique shape marker using a trained YOLOv8 model
- The drone picks up misplaced books using a magnetic attachment mechanism
- The drone transports books to their correct shelf positions
- The shelf uses ESP32-controlled electromagnets to lock books in place on drop-off
- The drone releases the book, verifies placement, and returns to base

---

## 2. Design Overview

### 2.1 Original Concepts Considered

Several design directions were explored and iterated on before arriving at the final system.

**Book identification** went through three full pivots. The original proposal used QR codes printed on book spines, which offered reliable encoding but required the drone camera to get close enough to resolve the code — a precision challenge for a hovering drone. This was replaced with ArUco markers, which are designed for computer vision and offer better detection at distance and angle. Eventually the approach shifted to bold geometric shape markers — vertical line, horizontal line, circle, square, cross, and X — which are visually distinct even at low resolution and under varying lighting conditions, and can be detected by a trained YOLO model without any external library dependency.

**Book pickup mechanism** also went through multiple iterations. The original design embedded neodymium rare earth magnets in the top of each book, with a matching magnet mounted on the drone underside. Testing revealed a critical flaw: the neodymium magnets were so strong that books on adjacent shelf slots attracted each other, causing the entire shelf to collapse. The design was revised to use a Towjug 20mm anisotropic flexible ferrite adhesive magnet on the drone underside, with M10×20×2mm carbon steel washers screwed into the top of each book. The flexible ferrite magnet is strong enough to hold a book during flight but weak enough not to disturb neighboring books on the shelf.

**Book design** also changed significantly. The original plan was to 3D print miniature books at 40×30×50mm with low infill. The first print batch failed because the super glue used to attach shape markers did not bond to PLA reliably. A brief detour into using single-digit 7-segment LED displays as books was explored but abandoned because the display face (14×19mm) was too small to fit a readable shape marker while also accommodating a washer. The final design returned to 3D printing at 22×25×30mm with a realistic book shape — front and back covers, spine bump, and page grooves — with M3 screw holes through the top and bottom to secure the washers mechanically rather than by adhesive.

### 2.2 Final Design Description

The final system consists of three integrated subsystems: the drone, the shelf, and the vision controller.

The drone is a DJI Tello with a Towjug 20mm adhesive ferrite magnet mounted to its underside via a 3D-printed payload clip (Printables model 479370). The drone runs a 5-phase autonomous task loop managed by `gpt_drone_controller.py`: DESCEND (move down 30cm at a time until the book is spotted), FIND_MAGNET (move down 20cm at a time until the washer is visible), COLLECT (fly forward and back to snap the magnet onto the washer), VERIFY (check whether the magnet is still on the book top — if gone, collection succeeded), and RETURN (ascend 50cm and land).

The shelf holds 6 book slots, each with an Adafruit P20/15 5V electromagnet underneath. When a book is dropped into a slot, the ESP32-S3 activates the corresponding relay channel, energizing the electromagnet which attracts the carbon steel washer at the bottom of the book and locks it in place.

Each book is 3D-printed PLA at 20% infill, 22×25×30mm, with an M3 screw securing an M10×20×2mm carbon steel washer to both the top and bottom. A bold shape marker — printed separately in black PLA and super-glued to the front face — identifies each book uniquely.

### 2.3 System Architecture

> *[System architecture diagram to be inserted here]*

### 2.4 How This Expands on Previous Work

This project integrates several domains that are typically treated separately: autonomous drone navigation, computer vision via large language models, electromagnetic actuation, and embedded systems control. No existing off-the-shelf system combines all four for the purpose of physical shelf management. The use of GPT-4o as a real-time drone navigation controller — not just for classification but for issuing movement commands — represents a novel application of vision-language models in physical robotics. The dual-network architecture (Tello WiFi for drone control + iPhone USB tethering for internet access) is a non-trivial systems integration challenge that had to be solved from scratch.

### 2.5 References and Schematics

> *[Wiring schematics and references to be inserted here]*

---

## 3. Preliminary Design Verification

### 3.1 Drone Payload Verification

Before committing to the magnetic pickup design, a full weight analysis was performed against the Tello's real-world payload limit of approximately 60g. The final drone-side components weigh approximately 7.3g total: Towjug adhesive magnet (~2.3g) and 3D-printed payload clip (~5g). This is well within the payload budget and leaves significant margin for any additional mounting hardware. The analysis explicitly rejected the option of mounting an electromagnet and microcontroller on the drone, which would have totaled approximately 45g and left no margin for error.

### 3.2 Shelf and Electromagnet Verification

The shelf subsystem was verified independently before integrating with the drone. The ESP32-S3 successfully activates individual relay channels via GPIO, energizing the Adafruit P20/15 electromagnets on demand. The 5V 5A wall adapter provides sufficient current for up to 6 electromagnets drawing ~400mA each. Books with carbon steel washers at the base were confirmed to be held securely in slots when the electromagnet is active and released cleanly when the electromagnet is deactivated.

### 3.3 GPT Vision API Verification

GPT-4o vision API connectivity was verified under the Tello WiFi constraint. When the laptop connects to the Tello's WiFi network, internet access is lost — the OpenAI API is unreachable. This was solved using iPhone USB tethering, which routes internet traffic through the phone's cellular data over a USB connection while leaving the laptop's WiFi adapter free for the Tello. With this setup, the GPT-4o API was confirmed reachable while the drone was connected and flying. In a controlled test, the drone took off, the GPT loop detected a Deer Park water bottle in the camera feed, printed `[GPT] Water spotted - landing now`, and the drone landed successfully.

---

## 4. Design Implementation

### 4.1 System Overview

The system operates as follows: the user presses START in the Tello controller UI, the drone takes off and stabilizes, the GPT vision loop begins scanning the camera feed, the drone descends toward the shelf, identifies a book, picks it up via magnetic attachment, transports it to the correct slot, the shelf electromagnet locks the book in place, and the drone returns. All three subsystems — drone, shelf, and vision controller — run simultaneously on a single laptop, communicating via WiFi (drone), serial USB (shelf), and HTTPS (OpenAI API).

### 4.2 DJI Tello Drone Subsystem

The drone subsystem is built on a custom `tello.py` wrapper around the Tello SDK. The key fix introduced in this project was adding `MOVE_DELAY = 3.0` seconds after every movement command. Without this delay, the Tello returns `error Not joystick` because it receives a new command before finishing the previous one. The `takeoff()` method includes a 3-second stabilization sleep after liftoff. All movement commands (`move_forward`, `move_down`, etc.) send raw SDK strings directly to the drone via UDP socket rather than going through the unit-converting `move()` method, which was found to produce out-of-range values when GPT returned distances in centimeters.

### 4.3 Smart Shelf Subsystem

The shelf uses an ESP32-S3-DevKitC-1-N8R8 connected to an ANMBEST 16-channel 5V optocoupler relay module. The relay module is wired with its VCC connected to the external 5V 5A wall adapter — not the ESP32's onboard 3.3V pin — so the optocoupler LEDs receive the full 5V they require. Each relay channel connects to one Adafruit P20/15 electromagnet. The ESP32 receives slot activation commands over serial from the main Python script and toggles the corresponding GPIO pin LOW to energize the relay.

### 4.4 GPT Vision Controller

`gpt_drone_controller.py` implements a 5-phase state machine. Each phase has its own GPT prompt that asks only the question relevant to that phase — no extraneous fields that GPT might hallucinate values for. Phase prompts ask for boolean fields only (`sees_bottle`, `sees_magnet`, `magnet_still_on_bottle`) to prevent GPT from returning out-of-range movement distances. The API is called at most once per 1.5 seconds to avoid rate limiting and excessive cost. JSON responses are stripped of markdown fences before parsing to handle GPT's tendency to wrap JSON in triple backticks.

### 4.5 Book Detection and Sorting Algorithm

Book identification uses the GPT-4o vision API via `Frame_converter.py`. Every 2 seconds, the video loop captures a frame and passes it to `FrameToSymbols.detect()` on a separate daemon thread so the video feed is never blocked. The frame is resized to a maximum of 640px on the longest side and JPEG-compressed at quality 70 before being base64-encoded and sent to GPT-4o with `detail: low`. The prompt asks GPT to return the six symbols it sees left to right as a comma-separated list with no extra text. The response is parsed and validated — if anything other than exactly 6 known symbols is returned, the result is dropped entirely.

`Dataset_generator.py` generates a 3000-image synthetic YOLO training dataset (500 images per class) of the six shape markers with randomized size, position, stroke thickness, brightness, Gaussian noise, and blur. The dataset is formatted in YOLO annotation format with a `data.yaml` file for potential offline training on Google Colab. The trained model was not used in the final implementation due to insufficient detection accuracy on real drone footage; GPT-4o vision was adopted as the detection backend instead.

`Book_Sorter.py` implements the sorting algorithm as a stateful class. On initialization it holds slots 0-5 and releases slot 8 (temp). It maintains a `hardware_slot_map` tracking which physical slots are currently held or released, and a `slot_map` mapping each symbol to its inferred physical slot based on the current frame and hardware state. The algorithm walks `CORRECT_ORDER` left to right, finds the first mismatch, and executes a 3-step swap using slot 8 as temp. Each step sets an `expected_frame` — the exact symbol order GPT should return after the user completes the move. If the next frame deviates from the expected frame, the algorithm detects the deviation, resets hardware state, and prints a warning. `Book_Sorter_Test.py` provides six offline test cases covering simple swap, repeated frames, two-swap sequences, deviation detection, already-correct shelf, and heavy disorder (3 swaps).

### 4.6 ESP32 Shelf Controller

`ESP32_Controller.ino` runs on the ESP32-S3 and manages 10 relay channels via GPIO pins `{4, 5, 6, 7, 15, 16, 17, 18, 8, 9}`. A `wiredOnNO[]` boolean array accounts for mixed NO/NC wiring — slots 0 and 1 are wired Normally Open (LOW energizes the relay), slots 2-9 are wired Normally Closed (HIGH energizes the relay). On startup, `relay_setup()` initializes all 10 slots to HOLDING state. The firmware listens on Serial at 115200 baud for newline-terminated commands: `hold <n>`, `release <n>`, `hold_all`, `release_all`, and `status`. `shelf_controller.py` on the Python side wraps `pyserial` and exposes matching `hold()`, `release()`, `hold_all()`, and `release_all()` methods that write these command strings over the serial connection.

### 4.7 3D Printed Books

All 3D-printed components were designed in OpenSCAD and printed in PLA at 20% infill.

**Shelf** — 245×30mm base, 3mm thick. 9 slots, 25mm wide per slot, 2mm walls between slots, 11mm wall height. Each slot has a 21mm diameter hole through the base centered in the slot for the Adafruit P20/15 electromagnet. Slot centers are at 14.5, 41.5, 68.5, 95.5, 122.5, 149.5, 176.5, 203.5, and 230.5mm.

**Enclosure bottom** — 249×33×1mm plate with 9 electromagnet holes (4.5mm M4 clearance) aligned to the shelf slot centers, and M3 corner mounting holes.

**Books** — 22×25×30mm with 3.2mm screw holes through the top and bottom center for M3 screws that secure the carbon steel washers. A shape marker tile printed separately in black PLA is super-glued to the front face of each book.

**Payload clip** — holds the Towjug 20mm ferrite magnet on the underside of the Tello. Attaches without modifying the drone body.

> *[Insert assembled book with washer and marker photos here]*

**OpenSCAD renders:**

**Shelf — isometric view:**
![Shelf isometric](https://raw.githubusercontent.com/SSOE-ECE1390/Drone-Based-Miniature-Book-Sorting-System/main/Images/shelf.png)

**Shelf — top view:**
![Shelf bottom](https://raw.githubusercontent.com/SSOE-ECE1390/Drone-Based-Miniature-Book-Sorting-System/main/Images/bottom.png)

**Books — isometric view:**
![Books isometric](https://raw.githubusercontent.com/SSOE-ECE1390/Drone-Based-Miniature-Book-Sorting-System/main/Images/book.png)

### 4.8 Inter-Subsystem Communication

Three network interfaces operate simultaneously on one laptop during a full system run. The laptop's WiFi adapter connects to the Tello's hotspot (192.168.10.1:8889) for drone control. An iPhone connected via USB cable provides cellular internet access through USB tethering, enabling OpenAI API calls. A USB-to-serial connection to the ESP32-S3 handles shelf electromagnet control. This architecture required solving the dual-network problem — Tello WiFi displaces internet access on the same adapter — which was resolved with iPhone USB tethering rather than a WiFi dongle.

### 4.9 Design Challenges

The project encountered and resolved a significant number of technical challenges across hardware and software.

`error Not joystick` from the Tello SDK was the most persistent drone-side issue. The drone returns this error when a new command arrives before the previous movement has completed. The fix was adding a class-level `MOVE_DELAY = 3.0` constant applied after every movement command in `tello.py`. The `gpt-4-vision-preview` model was deprecated mid-project with no advance warning, requiring an immediate switch to `gpt-4o` and a fix to the `image_url` format which changed from a plain string to a dictionary `{"url": "..."}` in the new client. A duplicate takeoff bug caused the drone to attempt takeoff twice — once from the UI and once from the GPT controller — with the second call hitting an already-airborne drone. This was resolved by moving takeoff out of the UI entirely. GPT consistently wrapped JSON responses in markdown fences, causing `json.JSONDecodeError`, resolved by stripping markdown fences before parsing.

---

## 5. Design Testing

### 5.1 Test Plan

Testing followed a progressive integration strategy: each subsystem was verified independently before being integrated with the others. The sequence was: drone takeoff and landing → GPT API connection under Tello WiFi → water bottle detection and landing → magnet pickup from stationary target → book shape detection → full system integration.

### 5.2 Drone Takeoff and Landing Tests

**Result: Pass.** The drone consistently responds to `takeoff` with `ok` and stabilizes within 3 seconds. The `land` command reliably brings the drone down. The `error Not joystick` issue was fully resolved after implementing `MOVE_DELAY`.

### 5.3 GPT Water Bottle Detection Test

**Result: Pass.** With iPhone USB tethering active and drone connected to Tello WiFi, the GPT-4o API was successfully reached. The drone took off, the vision loop scanned the camera feed, detected a Deer Park water bottle, printed `[GPT] Water spotted - landing now`, and landed. This test confirmed the full pipeline: takeoff → camera feed → GPT API → action execution → landing.

### 5.4 Magnet Pickup Test

> *[Pending — books not yet printed]*

### 5.5 Book Detection Test

> *[Pending — YOLO model not yet trained]*

### 5.6 Full System Integration Test

> *[Pending]*

### 5.7 Unsuccessful Attempts and Fixes

**Neodymium magnets on books** caused adjacent books on the shelf to attract each other and collapse the entire shelf. Replaced with carbon steel washers on books and a weak flexible ferrite magnet on the drone.

**3D printed books — washer attachment** initially used super glue to bond the carbon steel washers to PLA, which did not hold reliably under repeated magnetic pickup forces. The revised design uses M3×8mm countersunk screws to mechanically secure the washers into a pocket in the base of each book.

**10-slot shelf → 9-slot shelf** — the original shelf design had 10 slots but could not fit on the printer bed in a single run. Cut down to 9 slots to fit in one piece.

**QR codes → ArUco markers → shape markers** — three full pivots in identification strategy, each driven by a practical constraint. QR codes required too much drone precision to resolve. ArUco markers at book size were below reliable detection resolution from the drone camera. Shape markers are large, bold, and distinguishable even at low resolution and off-axis angles.

**`gpt-4-vision-preview` deprecated** mid-project with no warning. Required switching model to `gpt-4o`, updating the OpenAI client from legacy `openai.ChatCompletion.create` to `self.client.chat.completions.create`, and fixing the `image_url` format.

### 5.8 Demonstration Videos

> *[To be added]*

---

## 6. Bill of Materials

### 6.1 Hardware Components

| Component | Source | Part | Qty | Unit Price |
|-----------|--------|------|-----|------------|
| DJI Tello Drone | Ryze/DJI | — | 1 | — |
| 5V Electromagnet P20/15 | Adafruit | PID 3872 | 12 | $7.50 |
| ESP32-S3-DevKitC-1-N8R8 | Adafruit | PID 5336 | 1 | $19.95 |
| 16-Channel Relay Module | Amazon | ANMBEST | 1 | $16.99 |
| M10×20×2mm Carbon Steel Washers | Amazon | — | 1 pack | $6.19 |
| 5V 5A Wall Adapter w/ Screw Terminal | Amazon | — | 1 | $9.99 |
| Towjug Round Adhesive Magnets 20mm | Amazon | 30 pack | 1 | $3.99 |
| M3×8mm Countersunk Screws | Amazon | MewuDecor 50 pack | 1 | $5.99 |
| 3D Printed Drone Payload Clip | Printables | Model 479370 | 1 | $0 |
| 3D Printed Books PLA 20% infill | Printed | 22×25×30mm | 6 | — |

---

## 7. AI Usage Summary

### 7.1 Where AI Was Used


### 7.2 Example of AI Use

**Prompt:** "Can you look up this specific DJI Tello error: `error Not joystick`"

Claude fetched the official Tello SDK documentation and identified the root cause: the drone returns `error Not joystick` when a new command arrives before the previous movement has fully completed. The fix was adding a class-level `MOVE_DELAY = 3.0` constant applied after every movement command in `tello.py`.

The result was adapted from AI output — the root cause analysis was correct, but the specific constant value and placement required testing against the actual drone to confirm.

---

## 8. Summary, Conclusions and Future Work

### 8.1 Project Summary

This project delivered a working prototype of an autonomous drone-based book sorting system. The drone takes off, uses GPT-4o vision to navigate to a target, and a smart electromagnetic shelf controlled by an ESP32-S3 holds and releases books on command. The GPT-4o vision pipeline successfully detected a water bottle target and guided the drone to land on it in live testing. The book detection and sorting algorithm was implemented, tested offline against six test cases, and integrated into the live video pipeline. Full end-to-end autonomous sorting was demonstrated incrementally — drone navigation, shelf electromagnet control, and GPT-4o symbol detection all verified as working subsystems.

### 8.2 Conclusions

GPT-4o vision is a viable real-time controller for drone navigation at the prototype scale. The model reliably identifies visual targets, interprets spatial relationships, and returns structured JSON commands without requiring a trained local model. The dual-network constraint — Tello WiFi displacing internet access — was the single most impactful infrastructure challenge and was resolved cleanly with iPhone USB tethering. The electromagnetic shelf mechanism worked reliably for holding and releasing books. The primary gap between the prototype and a fully autonomous system is closing the drone-to-book positioning loop with enough precision for reliable magnetic pickup.

### 8.3 What I Would Do Differently

The YOLO training approach was a significant time investment that was ultimately not used. Starting directly with GPT-4o vision for symbol detection would have saved several weeks. The book pickup mechanism would benefit from a more rigid drone payload mount — the flexible ferrite magnet clip introduces positional uncertainty that makes precise pickup harder to guarantee. The shelf enclosure went through two full rebuilds due to wiring and slot assignment errors; a cleaner initial wiring diagram with labeled slots would have prevented both.

### 8.4 Future Work

The most immediate next step is completing the full autonomous pickup loop — descend, navigate to center over a book, descend to contact, verify magnetic attachment, transport to correct slot, and release. A more robust lateral navigation phase in `gpt_drone_controller.py` is needed for this, with GPT providing left/right/forward/back corrections until the book is centered under the drone. Longer term, the system could be scaled to a full-size shelf with a larger drone, a more powerful pickup mechanism, and a barcode or RFID-based identification system that does not depend on line-of-sight symbol detection.