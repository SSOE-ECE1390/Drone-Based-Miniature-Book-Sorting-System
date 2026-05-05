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
   - [3.3 Vision Model Verification](#33-vision-model-verification)
4. [Design Implementation](#4-design-implementation)
   - [4.1 System Overview](#41-system-overview)
   - [4.2 DJI Tello Drone Subsystem](#42-dji-tello-drone-subsystem)
   - [4.3 Smart Shelf Subsystem](#43-smart-shelf-subsystem)
   - [4.4 Vision Controller](#44-vision-controller)
   - [4.5 Book Detection and Sorting Algorithm](#45-book-detection-and-sorting-algorithm)
   - [4.6 ESP32 Shelf Controller](#46-esp32-shelf-controller)
   - [4.7 3D Printed Books](#47-3d-printed-books)
   - [4.8 Inter-Subsystem Communication](#48-inter-subsystem-communication)
   - [4.9 Design Challenges](#49-design-challenges)
   - [4.10 Controller UI](#410-controller-ui)
5. [Design Testing](#5-design-testing)
   - [5.1 Test Plan](#51-test-plan)
   - [5.2 Drone Takeoff and Landing Tests](#52-drone-takeoff-and-landing-tests)
   - [5.3 Book Sorter Test](#53-book-sorter-test)
   - [5.4 Unsuccessful Attempts and Fixes](#54-unsuccessful-attempts-and-fixes)
   - [5.5 Demonstration Videos](#55-demonstration-videos)
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

This project is an Autonomous Drone-Based Librarian System — a prototype that uses a DJI Tello drone to autonomously identify, pick up, and reorder miniature 3D-printed books on a smart electromagnetic shelf. The drone uses a YOLOv8n vision model to interpret its camera feed in real time, identify books by shape markers printed on their spines, and execute pick-and-place operations using a magnetic attachment mechanism. The shelf is controlled by an ESP32-S3 microcontroller that activates individual electromagnets to hold books securely in their assigned slots.

### 1.2 Motivation

The idea came directly from real library work experience. Manual shelf reading — walking the stacks, checking that every book is in its correct position — is one of the most repetitive and error-prone tasks in library operations. A single misplaced book can go unnoticed for weeks. This project asks: what if a drone could do that autonomously? Not just scan, but physically correct the order. That question is what drove every design decision from component selection to software architecture.

### 1.3 Project Goals

- A DJI Tello drone takes off autonomously and navigates a shelf using its onboard camera and YOLOv8n vision
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

**Book design** also changed significantly. The original plan was to 3D print miniature books at 40×30×50mm with low infill. The design was revised to 22×25×30mm with M3 screw holes through the top and bottom to secure the carbon steel washers mechanically — super glue did not hold the washers to PLA reliably under repeated magnetic pickup forces.

### 2.2 Final Design Description

The final system consists of three integrated subsystems: the drone, the shelf, and the vision controller.

The drone is a DJI Tello with a Towjug 20mm adhesive ferrite magnet adhered directly to its underside. The drone takes off, stabilizes, and hovers over the shelf. Its onboard camera feed is streamed live to the laptop, where a YOLO detection loop identifies the book spine symbols in each frame and passes them to the sorting algorithm.

The shelf holds 6 book slots, each with an Adafruit P20/15 5V electromagnet underneath. When a book is dropped into a slot, the ESP32-S3 activates the corresponding relay channel, energizing the electromagnet which attracts the carbon steel washer at the bottom of the book and locks it in place.

Each book is 3D-printed PLA at 20% infill, 22×25×30mm, with an M3 screw securing an M10×20×2mm carbon steel washer to both the top and bottom. A bold shape marker — printed separately in black PLA and super-glued to the front face — identifies each book uniquely.

### 2.3 System Architecture

```mermaid
%%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#ffffff', 'primaryBorderColor': '#000000', 'primaryTextColor': '#000000', 'clusterBkg': '#ffffff', 'clusterBorder': '#000000', 'lineColor': '#000000', 'edgeLabelBackground': '#ffffff', 'secondaryColor': '#ffffff', 'tertiaryColor': '#ffffff'}}}%%
flowchart TD
    subgraph Drone["DJI Tello Drone"]
        Camera["Onboard Camera - H.264 stream"]
        TelloPy["tello.py - Tello SDK wrapper"]
    end

    subgraph Host["Host Laptop"]
        main["main.py - Entry point"]
        TelloUI["tello_control_ui.py - PyQt5 UI"]
        FTS["Frame_converter.py - FrameToSymbols"]
        YOLO["best.pt - YOLOv8n local inference"]
        BS["Book_Sorter.py - Swap algorithm"]
        SC["shelf_controller.py - ShelfController"]
    end

    subgraph ESP32["ESP32-S3 + 16-ch Relay Module"]
        Arduino["ESP32_Controller.ino - Relay GPIO"]
        Slots05["Slots 0-5 - Shelf electromagnets"]
        Slots68["Slots 6-8 - Aux electromagnets"]
    end

    main --> TelloUI
    main --> SC
    TelloUI --> TelloPy
    TelloPy -->|WiFi UDP| Camera
    Camera -->|decoded frames| FTS
    FTS --> YOLO
    YOLO -->|ordered symbol list| BS
    BS --> SC
    BS --> TelloUI
    SC -->|serial 115200 baud| Arduino
   *Pending*

   #### Drone Controller Functionality

   The drone controller (`drone_controller.py`) implements autonomous navigation and target tracking. It uses a Kalman filter to smooth the detected position of the target book and computes control commands to center the drone over the book. The controller issues real-time movement commands to the drone based on the detected book's position and area in the camera frame, adjusting lateral, forward/backward, and up/down velocities. When the book is centered and close enough (area threshold), the controller stops the drone and can trigger a landing or pickup sequence. Safety limits and emergency stop logic are included to prevent erratic movement. The controller can be enabled or disabled for tracking, and provides telemetry for UI display.
    Arduino --> Slots68
```

### 2.4 How This Expands on Previous Work

This project combines autonomous drone flight, real-time YOLOv8 book spine detection, electromagnetic shelf actuation, and a confirmation-based multi-step sorting algorithm in a single integrated system. Each of these domains has been explored individually in prior work, but no existing system integrates all four for the purpose of physical shelf sorting. The confirmation-based swap algorithm — where each step waits for camera verification before advancing — adds a robustness layer that distinguishes this from simpler pick-and-place approaches.

### 2.5 References and Schematics

**Tello Python SDK** — `tello.py` is based on the official DJI Tello Python sample code: [github.com/dji-sdk/Tello-Python](https://github.com/dji-sdk/Tello-Python). The UDP socket architecture, H264 video decoding via `libh264decoder`, and Tkinter UI structure are all derived from the `Tello_Video` sample in that repository.

**Tello SDK 2.0 User Guide** — Official command reference for all SDK commands used (`takeoff`, `land`, `up`, `down`, `forward`, `back`, `left`, `right`, `cw`, `ccw`, `speed`, `battery?`, `streamon`): [dl-cdn.ryzerobotics.com/downloads/Tello/Tello%20SDK%202.0%20User%20Guide.pdf](https://dl-cdn.ryzerobotics.com/downloads/Tello/Tello%20SDK%202.0%20User%20Guide.pdf)

**ESP32-S3-DevKitC-1 Datasheet** — Pinout and GPIO reference used for relay wiring: [docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide.html)

**Adafruit Electromagnet P20/15 (PID 3872)** — Product page and datasheet: [adafruit.com/product/3872](https://www.adafruit.com/product/3872)

**Wiring — ESP32 and relay module:**

![Wiring](https://raw.githubusercontent.com/SSOE-ECE1390/Drone-Based-Miniature-Book-Sorting-System/main/Images/wire.jpg)

ESP32-S3 DevKitC plugged directly into the 16-channel relay module via jumper wires. 10 blue signal wires run out to the electromagnets under each shelf slot. Red and black power wires connect to the external 5V supply via a barrel jack adapter. A USB cable connects the ESP32 to the laptop for serial control.


   #### Drone Demo Videos

   <details>
   <summary><strong>Success: Drone Locates Book and Hovers</strong></summary>

   <video src="https://github.com/user-attachments/assets/2ec5e80e-eb16-4b18-9a4b-80602a0870c3" controls width="480"></video>

   <br/>
   In this run, the drone successfully navigates to the book using the configured distance settings, hovers close to the target, and lands safely.

   > [Full uncompressed video](video_demos/located_book_success.mp4)

   </details>

   <details>
   <summary><strong>Crash: Drone Locates Book and Crashes</strong></summary>

   <video src="https://github.com/user-attachments/assets/24025ef8-2d68-4dc7-9d4c-4a1f696bbad7" controls width="480"></video>

   <br/>
   In this run, the drone reaches the book but crashes upon arrival due to unstable flight or misconfiguration.

   > [Full uncompressed video](video_demos/located_book_crashed.mp4)

   </details>
---

## 3. Preliminary Design Verification

### 3.1 Drone Payload Verification

The DJI Tello has a real-world payload limit of approximately 60g. The full pickup assembly was verified as follows:

| Component | Weight |
|---|---|
| PLA book body (22×25×30mm, 20% infill) | ~8.4g |
| 2× M10×20×2mm carbon steel washer | ~7.4g |
| 2× M3×8mm carbon steel screw | ~1.0g |
| **Book assembly total** | **~16.8g** |
| Towjug 20mm adhesive ferrite magnet (drone underside) | ~2.3g |
| **Grand total** | **~19.1g** |

This is well within the 60g payload budget.

### 3.2 Shelf and Electromagnet Verification

The shelf subsystem was verified independently before integrating with the drone. The system uses 10 Adafruit P20/15 5V electromagnets, each drawing approximately 400mA at full activation.

**Power calculations:**

| Parameter | Value |
|---|---|
| Electromagnets | 10 |
| Current per electromagnet | 400mA |
| Total current (all active) | 4.0A |
| Supply voltage | 5V |
| Total power draw | 20W |

A 5V 5A DC barrel jack power supply was selected to meet the 4.0A peak demand with margin. The ESP32-S3 cannot power the 16-channel relay module directly — ESP32 GPIO pins are rated for a maximum of 12mA source/sink current each, which is far below the relay coil activation current. The relay module is therefore powered independently from the 5V 5A DC barrel jack supply, and the ESP32 GPIO pins only provide the low-current control signal to each relay's IN pin.

The ESP32-S3 successfully activates individual relay channels via GPIO, energizing the electromagnets on demand. Books with carbon steel washers at the base were confirmed to be held securely in slots when the electromagnet is active and released cleanly when deactivated.

### 3.3 Vision Model Verification

The YOLOv8n model (`best.pt`) runs entirely on the local machine — no internet connection is required for inference. This was an important design advantage over earlier cloud-based approaches: the drone's WiFi connection does not affect the vision pipeline at all. The model was verified to load and run in real time on the host laptop while connected to the Tello WiFi network, with no measurable impact on inference latency.

---

## 4. Design Implementation

### 4.1 System Overview

The user presses START in the Tello controller UI, the drone takes off and stabilizes, and the YOLO detection loop begins scanning the camera feed. The drone descends toward the shelf and the vision pipeline identifies the books and their spine symbols, which can be used to detect out-of-order books. All three subsystems — drone, shelf, and vision controller — run simultaneously on a single laptop, communicating via WiFi (drone), serial USB (shelf), and a local model inference pipeline (YOLO).

### 4.2 DJI Tello Drone Subsystem

The DJI Tello is a small consumer drone with a 5MP 720p camera, Wi-Fi connectivity, and a Tello SDK 2.0 interface for programmatic control. It communicates over UDP — commands are sent to port 8889, state data is received on port 8890, and the video stream is received on port 11111. The drone is controlled entirely via the `tello.py` wrapper, which sends SDK command strings over the UDP socket. Movement commands include `takeoff`, `land`, `up`, `down`, `forward`, `back`, `left`, `right`, and rotation via `cw`/`ccw`. The onboard camera streams H.264-encoded video which is decoded on the host laptop and fed into the YOLO detection pipeline.

### 4.3 Smart Shelf Subsystem

The shelf uses an ESP32-S3-DevKitC-1-N8R8 connected to an ANMBEST 16-channel 5V optocoupler relay module. The relay module is wired with its VCC connected to the external 5V 5A wall adapter — not the ESP32's onboard 3.3V pin — so the optocoupler LEDs receive the full 5V they require. Each relay channel connects to one Adafruit P20/15 electromagnet. The ESP32 receives slot activation commands over serial from the main Python script and toggles the corresponding GPIO pin LOW to energize the relay.

### 4.4 Vision Controller

The vision controller is implemented across `Frame_converter.py` and `Book_Sorter.py`. `Frame_converter.py` receives live frames from the drone's H.264 stream, runs YOLOv8n inference using `best.pt`, and returns an ordered list of detected book symbols (left to right) or `None` if fewer than 6 unique symbols are detected. `Book_Sorter.py` consumes that output on each frame tick, compares the detected order against the correct sequence, and drives the shelf controller to execute the appropriate hold/release commands for each swap operation.

### 4.5 Book Detection and Sorting Algorithm

Book identification uses a YOLOv8n model trained on real footage of the physical shelf across three scripts.

`frame.py` extracts every 15th non-blurry frame from approximately 15 recorded shelf videos using Laplacian variance filtering.

`dataset.py` processes those frames by detecting the white book faces via grayscale thresholding and contour detection, sorting boxes left to right, matching them against a per-video known label order, and outputting a YOLO-format annotated dataset with `data.yaml`.

`Dataset_train.py` is the Google Colab training script. It mounts Drive, rewrites `data.yaml` for Colab paths, trains YOLOv8n for 50 epochs at 640px with batch size 16 and early stopping at patience 15, validates and reports mAP, then saves `best.pt` back to Drive.

![Training Results](https://raw.githubusercontent.com/SSOE-ECE1390/Drone-Based-Miniature-Book-Sorting-System/main/Images/results.png)

The chart shows training and validation loss (box, classification, and DFL) alongside precision, recall, mAP@50, and mAP@50-95 across 42 epochs. All three loss curves drop sharply in the first 5 epochs and flatten cleanly, with no divergence between training and validation — indicating no overfitting. Precision and recall both converge to ~0.99, and mAP@50 and mAP@50-95 both reach ~1.0 by epoch 10 and hold steady for the remainder of training — strong results for a 6-class symbol detection task on a custom dataset.

`Frame_converter.py` loads `best.pt` at runtime and runs this model on every incoming drone frame. Below is an example detection — each book spine is identified with a bounding box and confidence score, sorted left to right into the symbol order passed to `BookSorter`:

![Detection frame with bounding boxes](https://raw.githubusercontent.com/SSOE-ECE1390/Drone-Based-Miniature-Book-Sorting-System/main/Images/frame.jpg)

`Frame_converter.py` loads `best.pt` at runtime, runs inference per frame, sorts detections left to right, and validates exactly 6 unique known symbols before returning the ordered list or `None`.

`Book_Sorter.py` receives the symbol list and executes a 4-step confirmation-based swap algorithm using slot 8 as temp. Each step sets an `expected_frame` and waits for camera confirmation before advancing. Step 4 confirms the completed swap and resets `last_frame` to None so the next mismatch check fires immediately. `Book_Sorter_Test.py` covers six offline test cases validating the full algorithm.

### 4.6 ESP32 Shelf Controller

`ESP32_Controller.ino` runs on the ESP32-S3 and manages 10 relay channels via GPIO pins `{4, 5, 6, 7, 15, 16, 17, 18, 8, 9}`. A `wiredOnNO[]` boolean array accounts for mixed NO/NC wiring — slots 0 and 1 are wired Normally Open (LOW energizes the relay), slots 2-9 are wired Normally Closed (HIGH energizes the relay). On startup, `relay_setup()` initializes all 10 slots to HOLDING state. The firmware listens on Serial at 115200 baud for newline-terminated commands: `hold <n>`, `release <n>`, `hold_all`, `release_all`, and `status`. `shelf_controller.py` on the Python side wraps `pyserial` and exposes matching `hold()`, `release()`, `hold_all()`, and `release_all()` methods that write these command strings over the serial connection.

### 4.7 3D Printed Books

All 3D-printed components were designed in OpenSCAD and printed in PLA at 20% infill.

**Shelf** — 245×30mm base, 3mm thick. 9 slots, 25mm wide per slot, 2mm walls between slots, 11mm wall height. Each slot has a 21mm diameter hole through the base centered in the slot for the Adafruit P20/15 electromagnet. Slot centers are at 14.5, 41.5, 68.5, 95.5, 122.5, 149.5, 176.5, 203.5, and 230.5mm.

**Enclosure bottom** — 249×33×1mm plate with 9 electromagnet holes (4.5mm M4 clearance) aligned to the shelf slot centers, and M3 corner mounting holes.

**Books** — 22×25×30mm with 3.2mm screw holes through the top and bottom center for M3 screws that secure the carbon steel washers. A shape marker tile printed separately in black PLA is super-glued to the front face of each book.

![Assembled book with washer and marker](https://raw.githubusercontent.com/SSOE-ECE1390/Drone-Based-Miniature-Book-Sorting-System/main/Images/shelf_book.JPG)

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

**16-channel relay module** had limited documentation, which made understanding the NO/NC wiring convention and optocoupler power requirements a significant learning curve early in the hardware build.

**Magnet and washer attachment** — getting the magnets and later the washers to stay on the books was a persistent challenge. The original 3D print design had to be revised to use screws, but the screw heads were not as flush as expected, which restricted the ferrite magnet on the drone from lying flat against the washer and reduced pickup reliability.

**Drone battery life** — the Tello is only capable of approximately 13–15 minutes of flight per battery. Additional batteries were ordered which allowed several hours of continuous testing per session rather than being limited to a single short flight.

**Dual-network constraint** — the laptop had to be simultaneously connected to the Tello's WiFi hotspot for drone control and to the internet for OpenAI API calls. These two connections cannot share the same WiFi adapter. Resolved using iPhone USB tethering to route internet traffic over cellular while keeping WiFi free for the Tello. This setup worked well for home testing but proved fragile in locations without reliable cellular coverage.

**3D printing precision** — getting hole sizes, wall thicknesses, and slot dimensions right required calculating everything down to the millimeter. This was made more critical by the Tello's payload constraint of approximately 50g, which meant every gram of the book design had to be accounted for to stay within the drone's lift capacity.

### 4.10 Controller UI

The controller UI is built in PyQt5 and split into two panels.

The left panel displays the live 640×480 H264 drone camera feed with START, STOP, and PAUSE controls below it.

The right panel shows drone connection status, a CORRECT ORDER reference strip, per-slot shelf state with symbols rendered green for correct and red for misplaced, hardware slot hold/release indicators, an active swap indicator, and a LAST ACTION log. Detection runs every 1 second on a daemon thread. A separate thread sends a keepalive `command` every 5 seconds.

![UI](https://raw.githubusercontent.com/SSOE-ECE1390/Drone-Based-Miniature-Book-Sorting-System/main/Images/UI.png)

![Swap](https://raw.githubusercontent.com/SSOE-ECE1390/Drone-Based-Miniature-Book-Sorting-System/main/Images/swap.jpg)

---

## 5. Design Testing

### 5.1 Test Plan

Testing followed a progressive integration strategy: each subsystem was verified independently before being integrated with the others. The sequence was: drone takeoff and landing → vision model local inference verification → water bottle detection and landing → magnet pickup from stationary target → book shape detection → full system integration.

`test_ui.py` was used to test the shelf controller in isolation — verifying that each relay channel could hold and release independently before connecting the drone.

![Shelf Controller Test UI](https://raw.githubusercontent.com/SSOE-ECE1390/Drone-Based-Miniature-Book-Sorting-System/main/Images/test.png)

### 5.2 Drone Takeoff and Landing Tests

**Result: Pass.** The drone consistently responds to `takeoff` with `ok` and stabilizes within 3 seconds. The `land` command reliably brings the drone down. The `error Not joystick` issue was fully resolved after implementing `MOVE_DELAY`.

### 5.3 Book Sorter Test

**Result: Pass.** `Book_Sorter_Test.py` validates the sorting algorithm in isolation using a `FakeShelf` that prints `HOLD`/`RELEASE` commands instead of driving the ESP32. Four test cases were run:

- **Test 1 — Simple swap:** Two out-of-order books (X at slot 0, I at slot 2) are swapped in three steps. The algorithm issues the correct hold/release sequence and reaches `CORRECT_ORDER`.
- **Test 2 — Repeated frames:** The same frame is fed multiple times while the user is slow to move a book. The algorithm suppresses duplicate commands and only advances state when the frame actually changes.
- **Test 3 — Two sequential swaps:** A shelf requiring two independent swaps is resolved completely. Each swap's three-step hold/release sequence executes correctly without interfering with the next.
- **Test 4 — Deviation detection:** The algorithm commands a specific move, but the user moves the wrong book. The sorter detects the mismatch and prints a `DEVIATION` warning rather than proceeding with incorrect state.

All four tests passed, confirming that the core swap logic, duplicate-frame suppression, and deviation detection all behave correctly before any drone or ESP32 hardware is involved.

### 5.4 Unsuccessful Attempts and Fixes

**Neodymium magnets on books** caused adjacent books on the shelf to attract each other and collapse the entire shelf. Replaced with carbon steel washers on books and a weak flexible ferrite magnet on the drone.

**3D printed books — washer attachment** initially used super glue to bond the carbon steel washers to PLA, which did not hold reliably under repeated magnetic pickup forces. The revised design uses M3×8mm countersunk screws to mechanically secure the washers into a pocket in the base of each book.

**10-slot shelf → 9-slot shelf** — the original shelf design had 10 slots but could not fit on the printer bed in a single run. Cut down to 9 slots to fit in one piece.

**QR codes → ArUco markers → shape markers** — three full pivots in identification strategy, each driven by a practical constraint. QR codes required too much drone precision to resolve. ArUco markers at book size were below reliable detection resolution from the drone camera. Shape markers are large, bold, and distinguishable even at low resolution and off-axis angles.

### 5.5 Demonstration Videos

#### Book Sorting

https://github.com/user-attachments/assets/a1bb452b-28a5-4dab-b7a9-c3783951165c

*Launching `main.py` → opening the Tello UI → sorting books using live image feed from the DJI Tello camera.*

> [Full uncompressed video](video_demos/book_sort_1.mp4)

#### Advanced Book Sorting

https://github.com/user-attachments/assets/b25b9f59-0693-4c01-8b49-99ffbe875736

*Launching `main.py` → opening the Tello UI → sorting books using live image feed from the DJI Tello camera (advanced multi-swap demonstration).*

> [Full uncompressed video](video_demos/book_sort_2_adv.mp4)

#### Drone Flying Commands

*Pending*

---

## 6. Bill of Materials

### 6.1 Hardware Components

| Component | Source | Part | Qty | Unit Price |
|-----------|--------|------|-----|------------|
| DJI Tello Drone | EAI Electronics | — | 1 | $219.00 |
| 5V Electromagnet P20/15 | Adafruit | PID 3872 | 12 | $7.50 |
| ESP32-S3-DevKitC-1-N8R8 | Adafruit | PID 5336 | 1 | $19.95 |
| 16-Channel Relay Module | Amazon | ANMBEST | 1 | $16.99 |
| M10×20×2mm Carbon Steel Washers | Amazon | — | 1 pack | $6.19 |
| 5V 5A Wall Adapter w/ Screw Terminal | Amazon | — | 1 | $9.99 |
| Towjug Round Adhesive Magnets 20mm | Amazon | 30 pack | 1 | $3.99 |
| M3×8mm Countersunk Screws | Amazon | MewuDecor 50 pack | 1 | $5.99 |

---

## 7. AI Usage Summary

### 7.1 Where AI Was Used

AI was used for debugging and error message interpretation throughout the project. When the Tello SDK returned unfamiliar error strings, Claude was used to look up their meaning against the official documentation and identify the root cause.

### 7.2 Example of AI Use

**Prompt:** "Can you look up this specific DJI Tello error: `error Not joystick`"

Claude fetched the official Tello SDK documentation and identified the root cause: the drone returns `error Not joystick` when a new command arrives before the previous movement has fully completed. The fix was adding a class-level `MOVE_DELAY = 3.0` constant applied after every movement command in `tello.py`.

The result was adapted from AI output — the root cause analysis was correct, but the specific constant value and placement required testing against the actual drone to confirm.

---

## 8. Summary, Conclusions and Future Work

### 8.1 Project Summary

This project delivered a working prototype of an autonomous drone-based book sorting system. The drone takes off, hovers over the shelf, and a smart electromagnetic shelf controlled by an ESP32-S3 holds and releases books on command. The book detection and sorting algorithm was implemented using YOLOv8n, tested offline against six test cases, and integrated into the live video pipeline. Full end-to-end autonomous sorting was demonstrated incrementally — drone navigation, shelf electromagnet control, and YOLOv8 symbol detection all verified as working subsystems.

### 8.2 Conclusions

The YOLOv8n model performed reliably on real drone footage, correctly identifying all six book spine symbols across varying lighting conditions and camera angles. The confirmation-based sorting algorithm handled multi-step physical swaps correctly — each step waiting for camera verification before advancing, preventing the system from declaring a swap complete before the physical move was confirmed. The dual-network constraint — Tello WiFi displacing internet access — was resolved cleanly with iPhone USB tethering. The electromagnetic shelf mechanism worked reliably for holding and releasing books. The primary gap between the prototype and a fully autonomous system is closing the drone-to-book positioning loop with enough precision for reliable magnetic pickup.

### 8.3 What I Would Do Differently

More research into drone flight dynamics before starting would have changed several early decisions. A lot of effort went into analyzing payload weight, but not enough into the actual complexities of stable hovering, precision positioning, and the effect of motor wash on a lightweight payload — all of which became real challenges during testing.

More research into magnetization would also have helped. The assumption was that the electromagnets would be significantly stronger than the ferrite magnet on the drone, but the actual magnetic force available was never properly calculated before committing to the design. A proper force analysis upfront would have caught this earlier.

The washer-based pickup mechanism did not produce the best outcome. If starting over, a different attachment approach would be explored — the washers introduced alignment sensitivity and inconsistency that made reliable pickup difficult to guarantee.

### 8.4 Future Work

The most important area for future work is the magnet system. Without a reliable pickup mechanism it was very difficult to demonstrate the drone completing a full pick-and-place cycle. The priority would be researching alternative attachment methods — the screw head sitting proud of the washer surface created too much gap between the drone magnet and the book, making reliable pickup inconsistent. Finding a flatter, more flush mounting solution for the washer, or replacing the washer entirely with a different ferromagnetic target, would be the first thing to tackle before attempting further autonomous sorting tests.