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

## **Training Model**

## **Code**

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

## **Additional Resources**

## **References**



