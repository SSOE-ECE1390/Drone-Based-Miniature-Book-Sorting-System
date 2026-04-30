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
   - [4.7 Inter-Subsystem Communication](#47-inter-subsystem-communication)
   - [4.8 Design Challenges](#48-design-challenges)
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

Each book is 3D-printed PLA at 20% infill, 22×25×30mm, with an M3×8mm countersunk screw securing an M10×20×2mm carbon steel washer at the top and bottom. A bold shape marker — printed separately in black PLA as an 18×18×1.5mm tile and super-glued to the front face — identifies each book uniquely.

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

Book identification uses a YOLOv8n model trained on a synthetic dataset generated by `generate_dataset.py`. The script generates 500 images per class (3000 total) of the six shape markers — vertical line, horizontal line, circle, square, cross, and X — with randomized size, position, stroke thickness, brightness, Gaussian noise, and blur to simulate real-world drone camera conditions. The dataset is formatted in YOLO annotation format with a `data.yaml` file and trained on Google Colab using a T4 GPU. The sorting algorithm compares the detected order against the correct sequence (Books 1–6) and generates the minimum set of swaps needed to restore correct order.

### 4.6 ESP32 Shelf Controller

`shelf_controller.py` manages the serial connection to the ESP32-S3 and exposes `activate_slot(n)` and `deactivate_slot(n)` methods. The ESP32 firmware listens for single-byte slot commands over UART and toggles the corresponding relay channel. The shelf and drone operate on separate networks and are coordinated by the main Python script running on the laptop.

### 4.7 Inter-Subsystem Communication

Three network interfaces operate simultaneously on one laptop during a full system run. The laptop's WiFi adapter connects to the Tello's hotspot (192.168.10.1:8889) for drone control. An iPhone connected via USB cable provides cellular internet access through USB tethering, enabling OpenAI API calls. A USB-to-serial connection to the ESP32-S3 handles shelf electromagnet control. This architecture required solving the dual-network problem — Tello WiFi displaces internet access on the same adapter — which was resolved with iPhone USB tethering rather than a WiFi dongle.

### 4.8 Design Challenges

The project encountered and resolved a significant number of technical challenges across hardware and software.

`error Not joystick` from the Tello SDK was the most persistent drone-side issue. The drone returns this error when a new command arrives before the previous movement has completed. The fix was adding a class-level `MOVE_DELAY = 3.0` constant applied after every movement command in `tello.py`. The `gpt-4-vision-preview` model was deprecated mid-project with no advance warning, requiring an immediate switch to `gpt-4o` and a fix to the `image_url` format which changed from a plain string to a dictionary `{"url": "..."}` in the new client. A duplicate takeoff bug caused the drone to attempt takeoff twice — once from the UI and once from the GPT controller — with the second call hitting an already-airborne drone. This was fixed by removing the takeoff call from `run_autonomous_task`. GPT consistently wrapped JSON responses in markdown fences, causing `json.JSONDecodeError`. Fixed by stripping ` ```json ``` ` before parsing. GPT returned `down 3000` as a distance value when the prompt asked for `distance_or_degrees`, exceeding the Tello's 500cm maximum. Fixed by removing distance fields from GPT prompts entirely and hardcoding safe values.

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

**7-segment LED displays as books** were explored as an alternative to 3D printing after the first book print batch failed. Abandoned because the 14×19mm face was too small to fit a shape marker alongside a washer mount.

**3D printed books — first attempt** failed because super glue did not reliably bond shape markers to PLA. The revised design uses mechanically screwed washers and a separate printed marker tile that is bonded to a clean flat surface under pressure.

**QR codes → ArUco markers → shape markers** — three full pivots in identification strategy, each driven by a practical constraint. QR codes required too much drone precision to resolve. ArUco markers at 14mm were borderline for drone camera resolution. Shape markers are large, bold, and distinguishable even at low resolution and off-axis angles.

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

Claude fetched the official Tello SDK documentation and confirmed that `down x` accepts values between 20 and 500cm only. It identified the root cause: the code was sending `down 3000` because GPT was returning 3000 as a distance value. The underlying issue was that the `move()` method in `tello.py` applied a unit conversion (×100 for meters to centimeters) on top of the value GPT already returned in centimeters, resulting in a 10× multiplier. The fix was removing distance fields from GPT prompts entirely and hardcoding safe values of 30cm and 20cm for the descent phases. Additionally, `MOVE_DELAY = 3.0` was added after every movement command to prevent the `Not joystick` error caused by commands firing before the previous movement completed.

The result was adapted from AI output — the root cause analysis was correct, but the specific fix required understanding how the GPT prompt interacted with the command pipeline, which required human judgment to implement correctly.

---

## 8. Summary, Conclusions and Future Work

### 8.1 Project Summary

> *[To be completed after full system demo]*

### 8.2 Conclusions

> *[To be completed after full system demo]*

### 8.3 What I Would Do Differently


### 8.4 Future Work

> *[To be completed]*
