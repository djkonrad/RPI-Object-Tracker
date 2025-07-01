# src/capture_sequence.py
import cv2
import time
import os
from picamera2 import Picamera2
# from libcamera import controls # This import is no longer strictly needed if using True/False
from picamera2.encoders import H264Encoder, Quality # For video encoding

def main():
    output_dir = "captured_media"
    os.makedirs(output_dir, exist_ok=True)

    print("Initializing Picamera2...")
    picam2 = Picamera2()

    try:
        # --- Configure and Capture Still Images ---
        still_config = picam2.create_still_configuration(main={"size": (1920, 1080), "format": "RGB888"}) # Full HD
        picam2.configure(still_config)
        picam2.start() # Start the camera in still capture mode

        num_images_to_capture = 3
        print(f"\nCapturing {num_images_to_capture} still images, 2 seconds apart.")

        # --- CORRECTED LINE FOR CAMERA CONTROLS ---
        # Use False for OFF, True for ON for boolean controls like AeEnable
        # You can remove this line entirely if you want auto-exposure/gain.
        picam2.set_controls({"AeEnable": False, "AnalogueGain": 1.0, "ExposureTime": 10000}) # Example: Fixed exposure
        # You might also use picam2.set_controls({"AwbEnable": False, "ColourGains": (1.0, 2.0)}) etc.

        for i in range(num_images_to_capture):
            image_path = os.path.join(output_dir, f"still_image_{i+1:02d}.jpg")
            
            picam2.capture_file(image_path)
            print(f"Saved still image: {image_path}")
            time.sleep(2) # Wait 2 seconds

        picam2.stop() # Stop the still capture mode

        # --- Configure and Capture Video ---
        print("\nAttempting to capture a 5-second video...")
        video_path = os.path.join(output_dir, "test_video.mp4") # MP4 is a common format

        video_config = picam2.create_video_configuration(main={"size": (1280, 720), "format": "RGB888"})
        picam2.configure(video_config)

        encoder = H264Encoder(10000000) # 10 Mbps bitrate
        
        picam2.start_recording(encoder, video_path, quality=Quality.HIGH)
        print(f"Recording video to: {video_path} for 5 seconds...")
        time.sleep(5) # Record for 5 seconds
        picam2.stop_recording() # Stop the video recording

        print(f"Video saved: {video_path}")

    except Exception as e:
        print(f"Error during camera operation: {e}")
        print("Please ensure 'picamera2' is installed and the camera module is correctly connected and enabled.")
        print("For installation: pip install picamera2")
        print("For camera enablement: sudo raspi-config -> Interface Options -> Camera")
        print("\nTroubleshooting Tip: If setting controls, try setting 'AeEnable': False/True directly.")
    finally:
        if picam2.started:
            picam2.stop()
        cv2.destroyAllWindows()
        print("Camera resources released. Check the 'captured_media' directory.")

if __name__ == "__main__":
    main()