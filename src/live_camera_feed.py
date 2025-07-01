# src/live_camera_feed.py
import cv2
import time
from picamera2 import Picamera2 # Import Picamera2

def main():
    print("Attempting to open camera using Picamera2...")
    
    # Initialize Picamera2
    picam2 = Picamera2()

    # Configure camera for video capture
    # You can adjust resolution here. Common sizes: (640, 480), (1280, 720)
    # Higher resolutions will consume more resources and may reduce FPS.
    # The default format is usually XRGB (or RGB), which needs conversion for OpenCV's BGR.
    video_config = picam2.create_video_configuration(main={"size": (640, 480)})
    picam2.configure(video_config)

    try:
        picam2.start() # Start the camera feed
        print("Camera opened successfully using Picamera2. Press 'q' to quit.")
        
        while True:
            # Capture a frame as a NumPy array (format: HxWxChannels, default: XRGB or RGB)
            # Picamera2 typically provides frames in RGB order if you choose that format,
            # but OpenCV imshow expects BGR. So, a conversion is often needed.
            frame = picam2.capture_array() 

            # Convert frame from RGB (Picamera2 default for `capture_array` often) to BGR (OpenCV default for `imshow`)
            # If your `picam2.create_video_configuration` specifies a different format, adjust accordingly.
            # Common Picamera2 output formats are XRGB, RGB888, YUV420 etc.
            # Assuming RGB888 or XRGB -> BGR conversion:
            bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # Display the frame
            cv2.imshow('Live Camera Feed (Press "q" to quit)', bgr_frame)

            # Wait for 'q' key press to exit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"Error: An issue occurred during camera operation: {e}")
        print("Please ensure 'picamera2' is installed and the camera module is correctly connected and enabled.")
        print("For installation: pip install picamera2")
        print("For camera enablement: sudo raspi-config -> Interface Options -> Camera")
    finally:
        picam2.stop() # Stop the camera feed
        cv2.destroyAllWindows()
        print("Camera released and windows closed.")

if __name__ == "__main__":
    main()