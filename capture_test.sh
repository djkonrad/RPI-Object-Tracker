#!/bin/bash
echo "Testing still image capture..."
libcamera-still -o test_image.jpg --width 640 --height 480
echo "Image saved as test_image.jpg"

echo "Testing short video capture (5 seconds)..."
libcamera-vid -o test_video.h264 -t 5000 --width 640 --height 480
echo "Video saved as test_video.h264"

echo "Listing captured files:"
ls -lh test_image.jpg test_video.h264
