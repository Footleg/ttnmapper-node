#!/usr/bin/env python3

# Install the rak811 library: sudo pip3 install rak811
# Upgrade the rak811 library: sudo pip3 install --upgrade rak811
# Install keyboard library: sudo pip3 install keyboard
# Requires ARIAL.TTF file in same folder as you run from

from random import randint
from sys import exit
from time import sleep

import subprocess

from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

import keyboard, sys

from rak811 import Mode, Rak811
from ttn_secrets import APPS_KEY, DEV_ADDR, NWKS_KEY

# Configuration: Time between LoRa pings (in seconds)
pinginterval = 60

# Create the I2C interface.
i2c = busio.I2C(SCL, SDA)

# Create the SSD1306 OLED class.
# The first two parameters are the pixel width and pixel height.  Change these
# to the right size for your display!
disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)

# Clear display.
disp.fill(0)
disp.show()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new("1", (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Load fonts
font = ImageFont.load_default()
fontbig = ImageFont.truetype("ARIAL.TTF", 36)
fontmid = ImageFont.truetype("ARIAL.TTF", 18)

# Get IP address
cmd = "hostname -I | cut -d\' \' -f1"
ip = subprocess.check_output(cmd, shell=True).decode("utf-8")

def showMessages(line3, line4):
	# Draw a black filled box to clear the image.
	draw.rectangle((0, 0, width, height), outline=0, fill=0)
	draw.text((x, top+0), "LoRa Mapper", font=font, fill=255)
	draw.text((x, top+8), "IP:"+ip, font=font, fill=255)
	draw.text((x, top+16), line3, font=font, fill=255)
	draw.text((x, top+24), line4, font=font, fill=255)
	disp.image(image)
	disp.show()

def showBigMessage(message):
	# Draw a black filled box to clear the image.
	draw.rectangle((0, 0, width, height), outline=0, fill=0)
	draw.text((x, top+0), message, font=fontbig, fill=255)
	disp.image(image)
	disp.show()
	
def showMidMessages(line1, line2):
	# Draw a black filled box to clear the image.
	draw.rectangle((0, 0, width, height), outline=0, fill=0)
	draw.text((x, top+0), line1, font=fontmid, fill=255)
	draw.text((x, top+16), line2, font=fontmid, fill=255)
	disp.image(image)
	disp.show()

def showSendInterval():
	showMidMessages("Updated send","interval: {}s".format(pinginterval))
	message = "New SF={}".format(sf)

def showSpreadFactor():
	showMidMessages("New spread factor","SF{}".format(sf))

# Create lora object
lora = Rak811()

# Most of the setup should happen only once...
print("Setup")
# Update display message
showMessages("Send interval {}s".format(pinginterval),"Setting Up LoRa Node")
lora.hard_reset()
lora.mode = Mode.LoRaWan
lora.band = "EU868"
lora.set_config(dev_addr=DEV_ADDR,
				apps_key=APPS_KEY,
				nwks_key=NWKS_KEY,
				adr="off")

# Update display message
showMessages("","Joining ABP")

print("Joining")
lora.join_abp()
lora.dr = 5
sf = 7
sent = 0

print("Sending packets every {}seconds - Interrupt to cancel loop".format(pinginterval))
print("You can send downlinks from the TTN console")

try:
	while True:
		print("Sending {} SF={}".format(sent+1,sf))
		showBigMessage("SF {}....".format(sf))
		# Cayenne lpp random value as analog
		lora.send(bytes.fromhex("0102{:04x}".format(randint(0, 0x7FFF))))
		sent +=1

		message = "SF{} Sent={}".format(sf,sent)
		showMessages(message,"Waiting for reply...")
		while lora.nb_downlinks:
			message = lora.get_downlink()["data"].hex()
			print("Received " + message)
			showMidMessages("Received", message)
			pause(10)
		
		#Pause and check for keyboard input
		for i in range(pinginterval):
			pause = 2
			dr = lora.dr
			if keyboard.is_pressed('0'):
				#Send now
				i = pinginterval
			elif keyboard.is_pressed('1'):
				#Decrease ping interval by 15s
				pinginterval -= 15
				if pinginterval < 15:
					pinginterval = 15
				showSendInterval()
			elif keyboard.is_pressed('2'):
				#Increase ping interval by 15s
				pinginterval += 15
				showSendInterval()
			elif keyboard.is_pressed('4'):
				#Set SF=7
				lora.dr=5
				sf = 7
			elif keyboard.is_pressed('5'):
				#Set SF=8
				lora.dr=4
				sf = 8
			elif keyboard.is_pressed('6'):
				#Set SF=9
				lora.dr=3
				sf = 9
			elif keyboard.is_pressed('7'):
				#Set SF=10
				lora.dr=2
				sf = 10
			elif keyboard.is_pressed('8'):
				#Set SF=11
				lora.dr=1
				sf = 11
			elif keyboard.is_pressed('9'):
				#Set SF=12
				lora.dr=0
				sf = 12
			else:
				showMidMessages(message,"Next trans {}s".format(pinginterval-i))
				pause = 1
				
			if dr != lora.dr:
				showSpreadFactor()
				message = "SF{} Sent={}".format(sf,sent)
				
			sleep(pause)
			
			if i >= pinginterval:
				break
			
except Exception as e:  # noqa: E722
	print("Unexpected error:", sys.exc_info()[0])
	print("",sys.exc_info()[1])
	print("",sys.exc_info()[2])
	showMessages("Unexpected error:",str(sys.exc_info()[1]))
	pass

print("Cleaning up")
lora.close()
exit(0)
