import io
import asyncio
import os
import time
import csv # Added for CSV writing
import matplotlib.pyplot as plt # Added for plotting
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder, Quality
from picamera2.outputs import FileOutput
from fastapi import FastAPI, WebSocket
from threading import Condition
from contextlib import asynccontextmanager
from tflite_runtime.interpreter import Interpreter
import numpy as np
import cv2


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        super().__init__()
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

    async def read(self):
        with self.condition:
            self.condition.wait()
            return self.frame


class JpegStream:
    def __init__(self):
        super().__init__() # Call parent constructor if JpegStream inherits from anything
        self.active = False
        self.connections = set()
        self.picam2 = None
        self.task = None

        # --- TFLite Model Setup ---
        self.model_path = os.path.join(os.path.dirname(__file__), "..", "models", "ssd_mobilenet_v2.tflite")
        self.labels_path = os.path.join(os.path.dirname(__file__), "..", "models", "coco_labels.txt") # Make sure this file exists with your class labels
        
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.labels = []
        self.input_height = None
        self.input_width = None

        # ⏱️ For performance monitoring
        self.inference_latencies_ms = [] # To store inference_ms for each frame
        self.total_latencies_ms = []    # To store total_ms for each frame
        self.fps_values = []            # To store calculated FPS per second
        self.frame_count_for_fps = 0    # Counter for FPS calculation
        self.fps_start_time = time.monotonic() # Timer for FPS calculation

    async def _load_model(self):
        """Loads the TFLite model and labels."""
        try:
            self.interpreter = Interpreter(model_path=self.model_path)
            self.interpreter.allocate_tensors()

            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            
            self.input_height, self.input_width = self.input_details[0]['shape'][1:3]

            with open(self.labels_path, 'r') as f:
                self.labels = [line.strip() for line in f.readlines()]
            
            print(f"Loaded TFLite model from {self.model_path}")
            print(f"Model input shape: {self.input_details[0]['shape']}, dtype: {self.input_details[0]['dtype']}")
        except Exception as e:
            print(f"Error loading TFLite model or labels: {e}")
            self.active = False # Ensure stream doesn't start if model loading fails
            raise # Re-raise to stop the application startup

    async def stream_jpeg(self):
        # Load model before starting camera
        if self.interpreter is None:
            await self._load_model()
            if not self.active: # If loading failed and active was set to False
                return

        self.picam2 = Picamera2()
        video_config = self.picam2.create_video_configuration(
            main={"size": (1920, 1080), "format": "RGB888"} # Using RGB888 for easier OpenCV integration
        )
        self.picam2.configure(video_config)
        output = StreamingOutput()
        self.picam2.start_recording(MJPEGEncoder(), FileOutput(output), Quality.MEDIUM)

        # Reset metrics when stream starts
        self.inference_latencies_ms = []
        self.total_latencies_ms = []
        self.fps_values = []
        self.frame_count_for_fps = 0
        self.fps_start_time = time.monotonic()


        try:
            while self.active:
                start_total_time = time.monotonic() # Start overall frame processing timer

                jpeg_data = await output.read()

                np_arr = np.frombuffer(jpeg_data, np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

                if img is None:
                    continue # Skip if frame decode fails

                # --- Preprocessing for TFLite Model ---
                start_preprocess_time = time.monotonic()
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_resized = cv2.resize(img_rgb, (self.input_width, self.input_height))
                input_data = np.expand_dims(img_resized, axis=0)
                
                # Normalize pixel values for FLOAT32 model input
                if self.input_details[0]['dtype'] == np.float32:
                    input_data = (np.float32(input_data) - 127.5) / 127.5 
                
                end_preprocess_time = time.monotonic()
                preprocess_ms = (end_preprocess_time - start_preprocess_time) * 1000

                self.interpreter.set_tensor(self.input_details[0]['index'], input_data)

                start_inference_time = time.monotonic()
                self.interpreter.invoke()
                end_inference_time = time.monotonic()
                inference_ms = (end_inference_time - start_inference_time) * 1000

                # --- Get detection results and Post-processing ---
                start_postprocess_time = time.monotonic()
                boxes = self.interpreter.get_tensor(self.output_details[0]['index'])[0]       
                classes = self.interpreter.get_tensor(self.output_details[1]['index'])[0]    
                scores = self.interpreter.get_tensor(self.output_details[2]['index'])[0]     
                num_detections = int(self.interpreter.get_tensor(self.output_details[3]['index'])[0]) 


                annotated_frame = img.copy() 
                im_h, im_w, _ = annotated_frame.shape
                
                detected_objects_summary = [] 

                for i in range(num_detections):
                    if scores[i] > 0.5: 
                        ymin, xmin, ymax, xmax = boxes[i]
                        x = int(xmin * im_w)
                        y = int(ymin * im_h)
                        w = int(xmax * im_w) - x
                        h = int(ymax * im_h) - y

                        class_id = int(classes[i])
                        label = self.labels[class_id] if class_id < len(self.labels) else "Unknown"
                        score = scores[i]

                        detected_objects_summary.append(label)

                        cv2.rectangle(annotated_frame, (x, y), (x + w, y + h), (0, 255, 0), 2) 
                        
                        label_text = f"{label}: {score:.2f}"
                        (text_width, text_height), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                        cv2.rectangle(annotated_frame, (x, y - text_height - baseline), (x + text_width, y), (0, 255, 0), -1)
                        cv2.putText(annotated_frame, label_text, (x, y - baseline), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

                end_postprocess_time = time.monotonic()
                postprocess_ms = (end_postprocess_time - start_postprocess_time) * 1000

                _, annotated_frame_jpeg = cv2.imencode('.jpg', annotated_frame)

                end_total_time = time.monotonic()
                total_ms = (end_total_time - start_total_time) * 1000

                # --- Collect Metrics ---
                self.inference_latencies_ms.append(inference_ms)
                self.total_latencies_ms.append(total_ms)

                self.frame_count_for_fps += 1
                current_time_for_fps = time.monotonic()
                elapsed_for_fps = current_time_for_fps - self.fps_start_time

                if elapsed_for_fps >= 1.0: # Calculate FPS every second
                    fps = self.frame_count_for_fps / elapsed_for_fps
                    self.fps_values.append(fps)
                    self.frame_count_for_fps = 0
                    self.fps_start_time = current_time_for_fps


                # --- Print Latency Statistics ---
                detected_counts = {}
                for obj in detected_objects_summary:
                    detected_counts[obj] = detected_counts.get(obj, 0) + 1
                
                objects_str = ", ".join([f"{count} {name}" for name, count in detected_counts.items()])
                if not objects_str:
                    objects_str = "No objects detected"

                input_shape_for_print = tuple(self.input_details[0]['shape'])

                print(f"0: {im_w}x{im_h} {objects_str}, {total_ms:.1f}ms")
                print(f"Speed: {preprocess_ms:.1f}ms preprocess, {inference_ms:.1f}ms inference, {postprocess_ms:.1f}ms postprocess per image at shape {input_shape_for_print}")


                tasks = [
                    websocket.send_bytes(annotated_frame_jpeg.tobytes())
                    for websocket in self.connections.copy()
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            if self.picam2:
                self.picam2.stop_recording()
                self.picam2.close()
                self.picam2 = None
            
            # Save metrics and plot when the stream stops
            self.save_metrics()

    def save_metrics(self):
        metrics_dir = os.path.join(os.path.dirname(__file__), "..", "metrics", "ssd")
        os.makedirs(metrics_dir, exist_ok=True) # Ensure directory exists

        # 💾 Save inference latency to CSV
        inference_csv_path = os.path.join(metrics_dir, "inference_metrics.csv")
        with open(inference_csv_path, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Frame", "Inference Latency (ms)"])
            for i, latency in enumerate(self.inference_latencies_ms):
                writer.writerow([i, latency])
        print(f"Saved inference metrics to: {inference_csv_path}")

        # 💾 Save FPS values to CSV
        fps_csv_path = os.path.join(metrics_dir, "fps_metrics.csv")
        with open(fps_csv_path, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Second", "FPS"])
            for i, fps in enumerate(self.fps_values):
                writer.writerow([i, fps])
        print(f"Saved FPS metrics to: {fps_csv_path}")

        # 📈 Plot and save performance metrics
        performance_plot_path = os.path.join(metrics_dir, "performance_metrics.png")
        plt.figure(figsize=(12, 5))
        
        plt.subplot(1, 2, 1)
        plt.plot(self.inference_latencies_ms, label="Inference Latency (ms)", color='blue')
        plt.xlabel("Frame Number")
        plt.ylabel("Latency (ms)")
        plt.title("Inference Latency per Frame (SSD MobileNet V2)")
        plt.grid(True)
        plt.legend()

        plt.subplot(1, 2, 2)
        plt.plot(self.fps_values, label="FPS", color="orange")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Frames per Second")
        plt.title("FPS Over Time (SSD MobileNet V2)")
        plt.grid(True)
        plt.legend()

        plt.tight_layout()
        plt.savefig(performance_plot_path)
        plt.close() # Close the plot to free memory
        print(f"Saved performance plot to: {performance_plot_path}")


    async def start(self):
        """Starts the JPEG stream and model loading."""
        if not self.active:
            self.active = True
            try:
                await self._load_model() 
            except Exception:
                print("Failed to load model, stream will not start.")
                self.active = False
                return
            
            self.task = asyncio.create_task(self.stream_jpeg())
            print("Stream start task initiated.")

    async def stop(self):
        """Stops the JPEG stream and releases resources."""
        if self.active:
            self.active = False # Set active to False to break the while loop in stream_jpeg
            if self.task:
                # Give some time for the stream_jpeg loop to exit gracefully
                if hasattr(jpeg_stream, 'output') and jpeg_stream.output:
                    with jpeg_stream.output.condition:
                        jpeg_stream.output.condition.notify_all()
                
                await asyncio.sleep(0.1) 
                if not self.task.done():
                    self.task.cancel() 
                try:
                    await self.task 
                except asyncio.CancelledError:
                    print("Stream task was explicitly cancelled.")
                except Exception as e:
                    print(f"Error awaiting stream task during stop: {e}")
                self.task = None
            print("Stream stopped and camera resources released.")


jpeg_stream = JpegStream()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup: Initializing stream components.")
    yield
    print("Application shutdown: Stopping stream gracefully.")
    await jpeg_stream.stop()


app = FastAPI(lifespan=lifespan)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    jpeg_stream.connections.add(websocket)
    print(f"WebSocket connected. Total clients: {len(jpeg_stream.connections)}")
        
    try:
        while True:
            await websocket.receive_text() 
    except Exception as e:
        print(f"WebSocket disconnected due to: {e}")
    finally:
        jpeg_stream.connections.remove(websocket)
        print(f"WebSocket disconnected. Remaining clients: {len(jpeg_stream.connections)}")
        if not jpeg_stream.connections and jpeg_stream.active:
            await jpeg_stream.stop()


@app.post("/start")
async def start_stream():
    """Endpoint to explicitly start the camera stream."""
    await jpeg_stream.start()
    return {"message": "Stream started via POST request"}


@app.post("/stop")
async def stop_stream():
    """Endpoint to explicitly stop the camera stream."""
    await jpeg_stream.stop()
    return {"message": "Stream stopped via POST request"}