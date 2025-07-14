# src/image_preprocessing_pipeline.py
import cv2
import numpy as np
import time
from picamera2 import Picamera2

def main():
    print("Opening camera for preprocessing demonstration using Picamera2...")
    
    # Initialize Picamera2
    picam2 = Picamera2()

    # Configure camera for video capture.
    video_config = picam2.create_video_configuration(main={"size": (640, 480), "format": "RGB888"})
    picam2.configure(video_config)

    # Define target size for ML model input (common examples: 300x300, 224x224)
    target_width, target_height = 300, 300

    try:
        picam2.start() # Start the camera feed

        # --- CORRECTED LINE FOR ACCESSING RESOLUTION ---
        # Access attributes using dot notation: .main.size
        # .size will return a tuple like (width, height)
        current_width = picam2.video_configuration.main.size[0]
        current_height = picam2.video_configuration.main.size[1]
        print(f"Camera opened. Original stream resolution: {current_width}x{current_height}")

        print(f"Processing frames to: {target_width}x{target_height} and converting to RGB (if not already).")
        print("Press 'q' to quit.")

        while True:
            frame_raw_rgb = picam2.capture_array() 

            # For Displaying Original Frame
            display_original_bgr = cv2.cvtColor(frame_raw_rgb, cv2.COLOR_RGB2BGR)
            cv2.imshow('Original Camera Feed (RGB from Picamera2 -> BGR for Display)', display_original_bgr)

            # Image Preprocessing Steps for ML Model
            resized_rgb_frame = cv2.resize(frame_raw_rgb, (target_width, target_height), interpolation=cv2.INTER_AREA)

            # Display Preprocessed Frame
            display_processed_bgr = cv2.cvtColor(resized_rgb_frame, cv2.COLOR_RGB2BGR)
            cv2.imshow(f'Processed Frame ({target_width}x{target_height} RGB -> BGR for Display)', display_processed_bgr)

            # Check for 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"Error: An issue occurred during camera operation or processing: {e}")
        print("Please ensure 'picamera2' is installed and the camera module is correctly connected and enabled.")
        print("For installation: pip install picamera2")
        print("For camera enablement: sudo raspi-config -> Interface Options -> Camera")
    finally:
        picam2.stop()
        cv2.destroyAllWindows()
        print("Camera released and windows closed.")
 
if __name__ == "__main__":
    main()