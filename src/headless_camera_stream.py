# src/headless_camera_stream.py
import cv2
from flask import Flask, Response

app = Flask(__name__)
camera = cv2.VideoCapture(0) # 0 for default camera

if not camera.isOpened():
    print("Error: Could not open camera for streaming.")
    print("Please ensure the camera module is connected correctly and enabled via 'sudo raspi-config'.")
    print("This script is intended for headless operation, accessible via web browser.")
    exit()

def generate_frames():
    """Generates frames from the camera for MJPEG streaming."""
    while True:
        success, frame = camera.read()
        if not success:
            print("Error: Failed to grab frame for streaming.")
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("Error: Failed to encode frame.")
                continue
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

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
    app.run(host='0.0.0.0', port=5000, threaded=True)