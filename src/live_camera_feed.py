# src/live_camera_feed.py
import cv2
import time

def main():
    print("Attempting to open camera...")
    # Use 0 for default camera. On some systems, 1 or -1 might be needed.
    # For Raspberry Pi, /dev/video0 is usually the CSI camera.
    # If using libcamera backend for OpenCV, it often just works with 0.
    cap = cv2.VideoCapture(0) 

    if not cap.isOpened():
        print("Error: Could not open camera.")
        print("Please ensure the camera module is connected correctly and enabled via 'sudo raspi-config'.")
        print("Also, check if 'opencv-python' (or opencv-python-headless if not for display) is installed.")
        print("If running headless, consider 'headless_camera_stream.py' instead.")
        return

    print("Camera opened successfully. Press 'q' to quit.")

    while True:
        ret, frame = cap.read() # Read a frame from the camera

        if not ret:
            print("Error: Failed to grab frame.")
            break

        # Display the frame
        cv2.imshow('Live Camera Feed (Press "q" to quit)', frame)

        # Wait for 'q' key press to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the camera and destroy all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()
    print("Camera released and windows closed.")

if __name__ == "__main__":
    main()