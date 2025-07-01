# src/headless_camera_stream.py
import cv2
from flask import Flask, Response
import time
from picamera2 import Picamera2 # Import Picamera2
import numpy as np # Needed for array manipulation

app = Flask(__name__)

# Initialize Picamera2
# It's good practice to initialize it globally if it's going to be reused across requests
# and explicitly handle its start/stop lifecycle.
# For simple streaming, starting it once and keeping it running is common.
picam2 = Picamera2()

# Configure camera for video capture
# Use a resolution suitable for web streaming. (640, 480) is a good starting point.
# Using 'RGB888' format ensures predictable color order for OpenCV conversion.
video_config = picam2.create_video_configuration(main={"size": (640, 480), "format": "RGB888"})
picam2.configure(video_config)

try:
    picam2.start() # Start the camera feed globally when the application starts
    print("Picamera2 started successfully for streaming.")
except Exception as e:
    print(f"Error: Could not start Picamera2 for streaming: {e}")
    print("Please ensure 'picamera2' is installed and the camera module is correctly connected and enabled.")
    print("For installation: pip install picamera2")
    print("For camera enablement: sudo raspi-config -> Interface Options -> Camera")
    # Exit if camera cannot be opened, as the app won't function without it.
    exit()

def generate_frames():
    """Generates frames from the camera for MJPEG streaming."""
    while True:
        try:
            # Capture a frame as a NumPy array (format: RGB888, as configured)
            frame = picam2.capture_array()

            # Convert frame from RGB (Picamera2 output) to BGR (OpenCV default for encoding)
            bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # Encode the frame as JPEG
            ret, buffer = cv2.imencode('.jpg', bgr_frame)
            if not ret:
                print("Error: Failed to encode frame as JPEG.")
                continue

            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            print(f"Error during frame generation: {e}")
            time.sleep(1) # Wait a bit before retrying to prevent rapid error logging

@app.route('/video_feed')
def video_feed():
    """Route to serve the MJPEG video stream."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    """Simple HTML page to embed the video feed."""
    return """
    <html>
    <head><title>Raspberry Pi Camera Stream</title></head>
    <body>
        <h1>Live Camera Stream</h1>
        <img src="/video_feed" width="640" height="480">
    </body>
    </html>
    """

if __name__ == '__main__':
    print("Starting Flask web server...")
    print("Access the stream from your browser at: http://<RaspberryPi_IP_Address>:5000")
    print("Press Ctrl+C to stop the server.")
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True)
    finally:
        # Ensure camera is stopped when the Flask app is shut down
        print("Stopping Picamera2...")
        picam2.stop()