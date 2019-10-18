#!/usr/bin/env python3

# Install the rak811 library: sudo pip3 install rak811
# Upgrade the rak811 library: sudo pip3 install --upgrade rak811
# Install keyboard library: sudo pip3 install keyboard
# Requires ARIAL.TTF file in same folder as you run from

import sys
from random import randint
from time import sleep

import subprocess

import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

#import keyboard
from digitalio import DigitalInOut, Direction, Pull

from rak811 import Mode, Rak811
from ttn_secrets import APPS_KEY, DEV_ADDR, NWKS_KEY

# Configuration: Time between LoRa pings (in seconds)
pinginterval = 60

# Mode of joystick. (1 = change spread factor, 2 = change ping interval)
mode = 1

# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)

# Create the SSD1306 OLED class.
# The first two parameters are the pixel width and pixel height.  Change these
# to the correct size for your display!
disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

# Configure GPIO pins for joystick and buttons on bonnet:
button_A = DigitalInOut(board.D5)
button_A.direction = Direction.INPUT
button_A.pull = Pull.UP
 
button_B = DigitalInOut(board.D6)
button_B.direction = Direction.INPUT
button_B.pull = Pull.UP
 
button_L = DigitalInOut(board.D27)
button_L.direction = Direction.INPUT
button_L.pull = Pull.UP
 
button_R = DigitalInOut(board.D23)
button_R.direction = Direction.INPUT
button_R.pull = Pull.UP

# NOTE we cannot use the joystick up position as it is used by the LoRa node pHAT
#      for the reset (needs to be configured as an output, not an input) 
#button_U = DigitalInOut(board.D17)
#button_U.direction = Direction.INPUT
#button_U.pull = Pull.UP
 
button_D = DigitalInOut(board.D22)
button_D.direction = Direction.INPUT
button_D.pull = Pull.UP
 
button_C = DigitalInOut(board.D4)
button_C.direction = Direction.INPUT
button_C.pull = Pull.UP


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

def showMessages(line1, line2, line3, line4):
	# Draw a black filled box to clear the image.
	draw.rectangle((0, 0, width, height), outline=0, fill=0)
	draw.text((x, top+0), line1, font=font, fill=255)
	draw.text((x, top+8), line2, font=font, fill=255)
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

def updateDr():
	if sf == 7:
		#Set SF=7
		lora.dr=5
	elif sf == 8:
		#Set SF=8
		lora.dr=4
	elif sf == 9:
		#Set SF=9
		lora.dr=3
	elif sf == 10:
		#Set SF=10
		lora.dr=2
	elif sf == 11:
		#Set SF=11
		lora.dr=1
	elif sf == 12:
		#Set SF=12
		lora.dr=0
	showMidMessages("New spread factor","SF{}".format(sf))

# Create lora object
lora = Rak811()

# Most of the setup should happen only once...
print("Setup")
# Update display message
showMessages("LoRa Mapper","IP:"+ip,"Send interval {}s".format(pinginterval),"Setting Up LoRa Node")
lora.hard_reset()
lora.mode = Mode.LoRaWan
lora.band = "EU868"
lora.set_config(dev_addr=DEV_ADDR,
				apps_key=APPS_KEY,
				nwks_key=NWKS_KEY,
				adr="off")

# Update display message
showMessages("LoRa Mapper","IP:"+ip,"","Joining ABP")

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
		showMessages("LoRa Mapper","IP:"+ip,message,"Waiting for reply...")
		while lora.nb_downlinks:
			message = lora.get_downlink()["data"].hex()
			print("Received " + message)
			showMidMessages("Received", message)
			sleep(10)
		
		#Pause until next ping and check for inputs
		joystickActive = 0
		i = 0
		while i < pinginterval:
			i += 1

			#Check for inputs
			if button_C.value == False:
				#Trigger next send now
				i = pinginterval
			elif button_D.value == False:
				while button_D.value == False:
					sleep(0.05)
				i -= (10 - joystickActive)
				joystickActive = 10
				pause = 0.05
				#Increment mode
				mode += 1
				if mode > 2:
					mode = 1
				if mode == 1:
					showMidMessages("Set SF","SF={}".format(sf))  
				elif mode == 2:
					showMidMessages("Set interval","Interval={}".format(pinginterval))
			elif button_L.value == False:
				while button_L.value == False:
					sleep(0.05)
				i -= (10 - joystickActive)
				joystickActive = 10
				pause = 0.05
				if mode == 1:
					#Decrease SF
					sf -= 1
					if sf < 7:
						sf = 7
					updateDr()
				elif mode == 2:
					#Decrease ping interval by 15s
					pinginterval -= 15
					if pinginterval < 15:
						pinginterval = 15
					showSendInterval()
			elif button_R.value == False:
				while button_R.value == False:
					sleep(0.05)
				i -= (10 - joystickActive)
				joystickActive = 10
				pause = 0.05
				if mode == 1:
					#Increase SF
					sf += 1
					if sf > 12:
						sf = 12
					updateDr()
				elif mode == 2:
					#Increase ping interval by 15s
					pinginterval += 15
					showSendInterval()
			elif joystickActive > 0:
				#Show menu settings messages and keep pause interval short
				joystickActive -= 1
			else:
				#Menu input activity ended, revert to 1 second pause and std status message
				showMidMessages("SF{} Sent={}".format(sf,sent),"Next trans {}s".format(pinginterval-i))
				pause = 1
				
			sleep(pause)
				
		#End Check for input loop
		
except Exception as e:  # noqa: E722
	print("Unexpected error:", sys.exc_info()[0])
	print("",sys.exc_info()[1])
	print("",sys.exc_info()[2])
	showMessages("LoRa Mapper","Unexpected error:",str(sys.exc_info()[1]),"")
	pass

print("Cleaning up")
lora.close()
sys.exit(0)
