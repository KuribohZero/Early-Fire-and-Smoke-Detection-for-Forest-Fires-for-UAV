import serial
import cv2

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
ser.flush()

command_ironbow = b'\xAA\x01\x05\x01\xBB' # Example byte sequence
ser.write(command_ironbow)