import io
import os
import time
import asyncio
import csv
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder, Quality
from picamera2.outputs import FileOutput
from fastapi import FastAPI, WebSocket
from threading import Condition
from contextlib import asynccontextmanager
from ultralytics import YOLO
import numpy as np
import cv2
import matplotlib.pyplot as plt  # <-- Added for plotting

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
        self.active = False
        self.connections = set()
        self.picam2 = None
        self.task = None
        self.model = YOLO("../models/yolov8n_ncnn_model")

        # ⏱️ For performance monitoring
        self.latencies = []
        self.fps_values = []
        self.last_time = time.perf_counter()
        self.frame_count = 0
        self.fps_start_time = time.perf_counter()

    async def stream_jpeg(self):
        self.picam2 = Picamera2()
        video_config = self.picam2.create_video_configuration(
            main={"size": (1920, 1080)}
        )
        self.picam2.configure(video_config)
        output = StreamingOutput()
        self.picam2.start_recording(MJPEGEncoder(), FileOutput(output), Quality.MEDIUM)

        try:
            while self.active:
                jpeg_data = await output.read()
                np_arr = np.frombuffer(jpeg_data, np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

                start_time = time.perf_counter()  # ⏱️ Start inference timer
                results = self.model(img)
                end_time = time.perf_counter()  # ⏱️ End inference timer

                latency = (end_time - start_time) * 1000 # Convert to milliseconds
                self.latencies.append(latency)

                self.frame_count += 1
                current_time = time.perf_counter()
                elapsed = current_time - self.fps_start_time

                if elapsed >= 1.0:
                    fps = self.frame_count / elapsed
                    self.fps_values.append(fps)
                    self.frame_count = 0
                    self.fps_start_time = current_time

                annotated_frame = results[0].plot()
                _, annotated_frame_jpeg = cv2.imencode('.jpg', annotated_frame)

                tasks = [
                    websocket.send_bytes(annotated_frame_jpeg.tobytes())
                    for websocket in self.connections.copy()
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            self.picam2.stop_recording()
            self.picam2.close()
            self.picam2 = None

            # Save metrics and plot
            self.save_metrics()

    def save_metrics(self):
        metrics_dir = os.path.join(os.path.dirname(__file__), "..", "metrics", "yolo")
        os.makedirs(metrics_dir, exist_ok=True) # Ensure directory exists

        # 💾 Save inference latency to CSV
        inference_csv_path = os.path.join(metrics_dir, "inference_metrics.csv")
        # 💾 Save to CSV
        with open(inference_csv_path, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Frame", "Latency (ms)"])
            for i, latency in enumerate(self.latencies):
                writer.writerow([i, latency])
        print(f"Saved inference metrics to: {inference_csv_path}")

        fps_csv_path = os.path.join(metrics_dir, "fps_metrics.csv")
        with open(fps_csv_path, "w", newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Second", "FPS"])
            for i, fps in enumerate(self.fps_values):
                writer.writerow([i, fps])
        print(f"Saved FPS metrics to: {fps_csv_path}")

        # 📈 Plot
        performance_plot_path = os.path.join(metrics_dir, "performance_metrics.png")
        plt.figure(figsize=(12, 5))
        plt.subplot(1, 2, 1)
        plt.plot(self.latencies, label="Inference Latency (ms)", color='blue')
        plt.xlabel("Frame Number")
        plt.ylabel("Latency (ms)")
        plt.title("Inference Latency per Frame (YOLO V8)")
        plt.grid(True)
        plt.legend()

        plt.subplot(1, 2, 2)
        plt.plot(self.fps_values, label="FPS", color="orange")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Frames per Second")
        plt.title("FPS Over Time (YOLO V8)")
        plt.grid(True)
        plt.legend()

        plt.tight_layout()
        plt.savefig(performance_plot_path)
        plt.close()
        print(f"Saved performance plot to: {performance_plot_path}")


    async def start(self):
        if not self.active:
            self.active = True
            self.task = asyncio.create_task(self.stream_jpeg())

    async def stop(self):
        if self.active:
            self.active = False
            if self.task:
                await self.task
                self.task = None

jpeg_stream = JpegStream()

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    print("done")
    await jpeg_stream.stop()

app = FastAPI(lifespan=lifespan)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    jpeg_stream.connections.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        jpeg_stream.connections.remove(websocket)
        if not jpeg_stream.connections:
            await jpeg_stream.stop()

@app.post("/start")
async def start_stream():
    await jpeg_stream.start()
    return {"message": "Stream started"}

@app.post("/stop")
async def stop_stream():
    await jpeg_stream.stop()
    return {"message": "Stream stopped"}
