## **Early Fire and Smoke Detection for Forest Fires for UAV**

This repository is for my final year project on the early detection of forest fires using UAV. The main focus of the code in this repository is real-time fire and smoke detection using raspberry pi 5 with hailo AI hat for using a visual raspberry pi camera and cvbs thermal camera. 

---

## **Table of Contents**

1. [Introduction](#introduction)
2. [Hardware](#hardware)
3. [Prequisites](#prerequisites)
4. [Installation](#installation)
5. [Training Model](#training-model)
6. [Code](#code)
7. [Additional Resources](#additional-resources)
8. [References](#references)

---

## **Introduction**




---

## **Hardware**

For the hardware section we will only cover the equipment we used.

Raspberry Pi components
- Raspberry Pi 5
- Raspberry AI hat
- Raspberry Pi Camera
- 25W Power Supply
Note:
For the raspberry pi the supplied header is too small so thing pins won't poke out of the AI hat board.
The ribbon cable connector for the Pi is thinner than the on the camera, requiring a ribbon cable with different width ends.
Raspberry Pi 5 is uses a 5V at 5A power supplier different from older Pi's which uses 5V at 3A. 

Thermal Camera
- Drone CVBS Thermal Camera
- Video Capture Card

Note:
Note possible to connect a CVBS thermal camera directly to the pi. Out specific camera has 5 terminals which include Vcc, GND, CVBS, tx and rx. Recommending 12V at 0.5A. 

Wiring:
12V PSU +   -> VCC
12V PSU GND -> GND
            -> RCA Shield (Capture Card Ground)

Camera CVBS -> RCA Centre (Capture Card Video in)
TX          -> RX (Raspberry Pi 5 Pin 10)
RX          -> TX (Raspberry Pi 5 Pin 8)
---

## **Prerequisites**

## **Installation**


AI hat installation https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html

sudo apt update && sudo apt full-upgrade sudo rpi-eeprom-update

if firmware is older than 6 December

sudo raspi-config Advanced Options -> Bootloader Version->Latest->Finish->Escape Key sudo rpi-eeprom-update -a sudo reboot

PCIe Gen 3.0 https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#pcie-gen-3-0

sudo raspi-config Advanced Options->PCIe Speed->Yes->Finish->Escape Key sudo reboot

AI Kit and AI HAT+ Software https://www.raspberrypi.com/documentation/computers/ai.html

sudo apt install hailo-all sudo reboot
=======
AI hat installation
https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html

sudo apt update && sudo apt full-upgrade
sudo rpi-eeprom-update

if firmware is older than 6 December

sudo raspi-config
Advanced Options -> Bootloader Version->Latest->Finish->Escape Key
sudo rpi-eeprom-update -a
sudo reboot

PCIe Gen 3.0
https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#pcie-gen-3-0

sudo raspi-config
Advanced Options->PCIe Speed->Yes->Finish->Escape Key
sudo reboot

AI Kit and AI HAT+ Software
https://www.raspberrypi.com/documentation/computers/ai.html

sudo apt install hailo-all
sudo reboot

## **Training Model**
Based off: https://github.com/hailo-ai/hailo-apps-infra/blob/main/doc/developer_guide/retraining_example.md
Hardware:
- CPU: AMD Ryzen 5 2600 Six-Core Processor
- GPU: AMD 7800 XT

Installing Hailo AI Suite
https://hailo.ai/developer-zone/documentation/2025-07-for-hailo-8-8l/?sp_referrer=suite/versions_compatibility.html
sudo apt-get install python3.12-dev python3-tk graphviz libgraphviz-dev

sudo apt-get install -y ffmpeg x11-utils libgstreamer-plugins-base1.0-dev python-gi-dev libgirepository1.0-dev libzmq3-dev



yolo export model=/home/jugmentz/yolo_runs/fire_focus_run3/weights/best.pt imgsz=640 format=onnx opset=11

hailomz compile yolov11n \
  --ckpt /home/jugmentz/yolo_runs/fire_focus_run3/weights/best.onnx \
  --hw-arch hailo8l \
  --calib-path /home/jugmentz/Documents/dataset/Annotated/Test2/images \
  --yaml /home/jugmentz/Documents/dataset/Annotated/YOLO_dataset3/dataset.yaml \
  --labels-json /home/jugmentz/Documents/dataset/Annotated/labels.json \
  --classes 2 \
  --performance



Based off: https://github.com/hailo-ai/hailo-apps-infra/blob/main/doc/developer_guide/retraining_example.md Hardware:

    CPU: AMD Ryzen 5 2600 Six-Core Processor
    GPU: AMD 7800 XT

Installing Hailo AI Suite https://hailo.ai/developer-zone/documentation/2025-07-for-hailo-8-8l/?sp_referrer=suite/versions_compatibility.html sudo apt-get install python3.12-dev python3-tk graphviz libgraphviz-dev

sudo apt-get install -y ffmpeg x11-utils libgstreamer-plugins-base1.0-dev python-gi-dev libgirepository1.0-dev libzmq3-dev

yolo export model=/home/jugmentz/yolo_runs/fire_focus_run3/weights/best.pt imgsz=640 format=onnx opset=11

hailomz compile yolov11n
--ckpt /home/jugmentz/yolo_runs/fire_focus_run3/weights/best.onnx
--hw-arch hailo8l
--calib-path /home/jugmentz/Documents/dataset/Annotated/Test2/images
--yaml /home/jugmentz/Documents/dataset/Annotated/YOLO_dataset3/dataset.yaml
--labels-json /home/jugmentz/Documents/dataset/Annotated/labels.json
--classes 2
--performance

## **Code**
docker rm -f firedetectionappcontainer \
docker build -t firedetectionapp .
docker run -d --name firedetectionappcontainer -p 8000:8000 firedetectionapp

First Page
Pi Connection
Thermal Camera Check
Visual Camera Check
Drone Status:
Last Update
Battery Power
Altitude
GPS position
Flight Time

Send Test Image

The program works like this:

- The camera 
    - Dawn  -> Thermal Camera used majority of the time + Visual Camera every two minutes
    - Day   -> Visual Camera used majority of the time + Thermal Camera every 10 minutes
    - Dusk  -> Visual Camera used majority of the time + Thermal Camera every two minutes
    - Night -> Thermal Camera used majority of the time + Visual Camera every 10 minutes

- Once a fire is detected a image and a message on the location will be send from the pi to the computer
- Operators confirms fire
- Drone starts streaming the detected fire for both visual and thermal images

python3 -m venv --system-site-packages venv
source venv/bin/activate
## **Additional Resources**

## **References**



