# Real-Time Object Detection System - Raspberry Pi Setup Guide

This guide details the steps to set up your Raspberry Pi and camera module, as well as the necessary software environment, for the Real-Time Object Detection System project.

## 1. Hardware Requirements

* Raspberry Pi 4 Model B
* Raspberry Pi Camera Module V2 (or compatible CSI camera module)
* MicroSD card (minimum 16GB, Class 10 or higher recommended)

## 2. Software Requirements

* Raspberry Pi Imager
* SSH client (e.g., PuTTY for Windows, built-in terminal for Linux/macOS)
* Git (for cloning this repository)
* Python 3.x
* Python `pip` package manager
* OpenCV Python library

## 3. Raspberry Pi OS Initial Configuration

### 3.1. Enable Camera Interface

If you didn't enable it during the OS flashing, or if you're using an older OS version:

1.  Open a terminal on your Raspberry Pi (or connect via SSH).
2.  Run the command:
    ```bash
    sudo raspi-config
    ```
3.  Navigate to `3 Interface Options` > `P1 Camera` > `Yes` to enable the camera interface.
4.  Exit `raspi-config` and reboot your Raspberry Pi if prompted.

### 3.2. Update & Upgrade OS

Ensure Raspberry Pi OS is up to date:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo rpi-update # Only if experiencing kernel/firmware issues, use with caution
sudo reboot
```

## 4. Install Python Environment and Dependencies

### 4.1. Install Git and Python Dev Tools

```
sudo apt install git python3-pip python3-dev -y
```

### 4.2. Clone the Project Repository

Navigate to desired directory (e.g., home directory) and clone this project:
```
cd ~
git clone https://github.com/djkonrad/RPI-Object-Tracker.git
cd rpi-object-detector
```

### 4.3. Create and Activate a Python Virtual Environment
It's best practice to use a virtual environment to manage project dependencies:

```
python3 -m venv --system-site-package venv
source venv/bin/activate
```

### 4.4. Install Project Python Dependencies
Inside virtual environment, install the necessary Python libraries.

```
pip install numpy
pip install opencv-python # Or pip install opencv-python-headless
# Other potential libraries will be added later, e.g., tensorflow, tflite_runtime
```


