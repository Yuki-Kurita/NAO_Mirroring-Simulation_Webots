# -*- coding: utf-8 -*-

from __future__ import print_function
from contextlib import closing
from naoqi import ALProxy
import xml.etree.ElementTree as ET
import socket
import sys
import requests
import time
import scp

# ---- scp transpotation ----
# Input nao's IP and user name ** nao's IP address changes sometimes
IP = "163.221.38.249"
user_name = 'nao'

leds = ALProxy("ALLeds", IP, 9559)
# motion instance
motion = ALProxy("ALMotion", IP, 9559)
posture = ALProxy("ALRobotPosture", IP, 9559)
# Create a new LED group
name="FaceLeds"
colorName="cyan"
duration=1

motion.rest()
