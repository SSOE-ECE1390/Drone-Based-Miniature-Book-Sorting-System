# Drone-Based Miniature Book Sorting System (Image Processing Focus)

## Team Information
- **Name:** Wunmi [Your Last Name]  
- **Email:** ooos6@pitt.edu  

## Project Description
This project is developed in combination with **ECE 1895 (Junior Design Fundamentals)**. In ECE 1895, the focus is on the hardware and system integration. In ECE 1390, the focus is on the image processing pipeline.  

The project uses a DJI Tello drone with a lightweight 3D-printed attachment to sort and reshelve miniature books. The drone’s onboard camera captures images of a miniature shelf environment, which are processed in Python to determine correct shelf placement locations. The results of the image processing guide the placement actions carried out in the overall system.  

---

## Image Processing Methods and Tools
- **Programming Language:** Python  
- **Libraries:** OpenCV, NumPy, Matplotlib  

### Techniques Applied  
- **Thresholding:** Separate shelves and books from the background.  
- **Edge Detection:** Detect shelf boundaries and book outlines.  
- **Morphological Operations:** Reduce noise and refine masks.  
- **Segmentation:** Partition the image into regions (books, shelves, background).  

---

## Integration with ECE 1895 (Junior Design)
The image processing developed in this course is connected to the system design in ECE 1895. The process is:  
1. The drone captures images of the shelf.  
2. Images are processed in Python using algorithms such as thresholding, edge detection, morphological operations, and segmentation.  
3. The output from image processing determines the correct placement instructions.  
4. These instructions are used by the system in ECE 1895 to carry out physical book placement.  

---

## Milestones
- **Week 1:** Define image processing objectives and set up Python environment.  
- **Week 2:** Implement initial thresholding pipeline.  
- **Week 3 (Milestone):** Apply edge detection and segmentation to identify shelves and books.  
- **Week 4:** Use morphological operations to improve accuracy.  
- **Week 5:** Validate the pipeline with varied images.  
- **Week 6:** Document results and prepare final presentation.  

---

## Final Demonstration
The final demonstration will show how images of a miniature library setup are processed to:  
1. Detect shelves and book locations.  
2. Identify the correct placement slot for each book.  
3. Provide results that connect to the ECE 1895 project, where the drone performs the physical placement.  
