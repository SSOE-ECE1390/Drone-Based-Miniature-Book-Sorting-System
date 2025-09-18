# Drone-Based Miniature Book Sorting System (Image Processing Focus)

## Team Information
- **Name:** Wunmi [Your Last Name]  
- **Email:** ooos6@pitt.edu  

## Project Description
This project explores how image processing techniques can be applied to automate the task of sorting and reshelving miniature books. The system uses a DJI Tello drone with its onboard camera to capture images of a miniature shelf environment. These images are analyzed in Python to determine shelf locations and guide placement decisions for miniature books.  

While the hardware platform provides the physical demonstration, the focus in this course is on the **image processing pipeline**—how to transform raw images into meaningful information that can be used for automated decision-making. The outcome will highlight how techniques learned in this course can be applied to a practical problem that integrates with, but is not dependent on, hardware control.  

---

## Image Processing Methods and Tools
- **Programming Language:** Python  
- **Libraries:** OpenCV, NumPy, Matplotlib (for visualization)  

### Techniques Applied  
- **Thresholding:** Separate books and shelf areas from the background based on intensity or color.  
- **Edge Detection:** Identify shelf boundaries and book outlines.  
- **Morphological Operations:** Refine masks, remove noise, and enhance structural features in processed images.  
- **Segmentation:** Divide the image into regions (books vs. shelf vs. background) for classification and placement.  

---

## Integration with Hardware
Although hardware is not the focus, the processed image data will serve as input to the drone’s control logic:  
1. The drone captures an image of the shelf.  
2. The image is processed using thresholding, edge detection, and morphological operations to identify correct shelf locations.  
3. The results are translated into placement instructions that the drone can execute through its lightweight 3D-printed attachment.  

This integration demonstrates how image processing supports real-world automation, while the majority of technical work is concentrated in the image analysis itself.  

---

## Milestones
- **Week 1:** Define image processing objectives and set up Python environment.  
- **Week 2:** Implement initial thresholding pipeline to isolate shelves and books.  
- **Week 3 (Milestone):** Apply edge detection and segmentation to identify shelf boundaries and book placement locations.  
- **Week 4:** Integrate morphological operations for noise reduction and improve detection accuracy.  
- **Week 5:** Test pipeline with varied images and validate placement accuracy.  
- **Week 6:** Document results and prepare final presentation.  

---

## Final Demonstration
The final demonstration will show how images of a miniature library setup can be processed to:  
1. Detect shelf regions and book locations.  
2. Determine the correct placement slot for a book.  
3. Provide these results as instructions for the drone to physically complete the task.  

The success of the project will be evaluated based on the accuracy and robustness of the image processing pipeline, with hardware acting only as the execution platform.  
