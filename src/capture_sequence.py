# src/capture_sequence.py
import cv2
import time
import os

def main():
    output_dir = "captured_images"
    os.makedirs(output_dir, exist_ok=True)

    print(f"Opening camera for image capture. Images will be saved to '{output_dir}/'.")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        print("Ensure camera module is connected and enabled. Check 'sudo raspi-config'.")
        return

    num_images_to_capture = 5
    print(f"Capturing {num_images_to_capture} images, 1 second apart.")

    for i in range(num_images_to_capture):
        ret, frame = cap.read()
        if not ret:
            print(f"Error: Failed to grab frame {i+1}.")
            break

        image_path = os.path.join(output_dir, f"frame_{i+1:02d}.jpg")
        cv2.imwrite(image_path, frame)
        print(f"Saved: {image_path}")
        time.sleep(1) # Wait 1 second

    print("\nAttempting to capture a 5-second video...")
    video_path = os.path.join(output_dir, "test_video.avi")
    # Define the codec and create VideoWriter object
    # Adjust resolution and FPS based on your camera/Pi capabilities and desired output
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = 10 # Frames per second for recording
    fourcc = cv2.VideoWriter_fourcc(*'MJPG') # Codec for AVI

    out = cv2.VideoWriter(video_path, fourcc, fps, (frame_width, frame_height))

    start_time = time.time()
    while (time.time() - start_time) < 5: # Record for 5 seconds
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame during video recording.")
            break
        out.write(frame)

    print(f"Saved video: {video_path}")

    # Release everything if job is finished
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print("Camera released. Check the 'captured_images' directory.")

if __name__ == "__main__":
    main()