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
selectedPingInterval = 60
minPingInterval = 10
activePingInterval = selectedPingInterval
rapidPingCount = 0

# Menu mode of joystick. (1=change spread factor, 2=change ping interval, 3=button A operation)
menuMode = 1
menuActiveTime = 100 #Now many loop cycles the menu messages stay showing

#Mode of buttons (1=4 pings at minimum time intervals, 2-7=instance ping at SF7-12)
btnAMode = 1
btnBMode = 5
btnAModeMsg = ""
btnBModeMsg = ""

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
padding = -1
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Load fonts
#font = ImageFont.load_default()
fontbig = ImageFont.truetype("ARIAL.TTF", 36)
fontmid = ImageFont.truetype("ARIAL.TTF", 18)
fontsmall = ImageFont.truetype("ARIAL.TTF", 12)

# Get IP address
cmd = "hostname -I | cut -d\' \' -f1"
ip = subprocess.check_output(cmd, shell=True).decode("utf-8")

def showMessages(line1, line2="", line3="", line4=""):
	lineHeight = 12
	# Draw a black filled box to clear the image.
	draw.rectangle((0, 0, width, height), outline=0, fill=0)
	draw.text((x, top+0), line1, font=fontsmall, fill=255)
	draw.text((x, top+lineHeight), line2, font=fontsmall, fill=255)
	draw.text((x, top+2*lineHeight), line3, font=fontsmall, fill=255)
	draw.text((x, top+3*lineHeight), line4, font=fontsmall, fill=255)
	disp.image(image)
	disp.show()

def showBigMessage(message):
	# Draw a black filled box to clear the image.
	draw.rectangle((0, 0, width, height), outline=0, fill=0)
	draw.text((x, top+0), message, font=fontbig, fill=255)
	disp.image(image)
	disp.show()
	
def showMidMessages(line1, line2="", line3="", line3small=False):
	lineHeight = 18
	
	if line3small:
		line3font=fontsmall
		line3Spacer = 16
	else:
		line3font=fontmid
		line3Spacer = 0
		
	# Draw a black filled box to clear the image.
	draw.rectangle((0, 0, width, height), outline=0, fill=0)
	draw.text((x, top+0), line1, font=fontmid, fill=255)
	draw.text((x, top+lineHeight), line2, font=fontmid, fill=255)
	draw.text((x, top+2*lineHeight+line3Spacer), line3, font=line3font, fill=255)
	disp.image(image)
	disp.show()

def showSendInterval():
	showMidMessages("Updated send","interval: {}s".format(selectedPingInterval))

def showBtnAMode():
	global btnAModeMsg
	if btnAMode == 1:
		showMidMessages("Set btn #5 mode","Send next 4","at {}s intervals".format(minPingInterval))
		btnAModeMsg = "#5: 4x{}s".format(minPingInterval)
	else:
		showMidMessages("Set btn #5 mode","Instant send at","SF{}".format(btnAMode+5) )
		btnAModeMsg = "#5: SF{}".format(btnAMode+5)
	
def showBtnBMode():
	global btnBModeMsg
	if btnBMode == 1:
		showMidMessages("Set btn #6 mode","Send next 4","at {}s intervals".format(minPingInterval))
		btnBModeMsg = "#6: 4x{}s".format(minPingInterval)
	else:
		showMidMessages("Set btn #6 mode","Instant send at","SF{}".format(btnBMode+5) )
		btnBModeMsg = "#6: SF{}".format(btnBMode+5)
	
def updateDr(sFactor):
	if sFactor == 7:
		#Set SF=7
		lora.dr=5
	elif sFactor == 8:
		#Set SF=8
		lora.dr=4
	elif sFactor == 9:
		#Set SF=9
		lora.dr=3
	elif sFactor == 10:
		#Set SF=10
		lora.dr=2
	elif sFactor == 11:
		#Set SF=11
		lora.dr=1
	elif sFactor == 12:
		#Set SF=12
		lora.dr=0
	showMidMessages("Spread factor","set to SF{}".format(sFactor))

def activateRapidPings(counter):
	global rapidPingCount, activePingInterval
	
	if rapidPingCount == 0:
		#Set rapid ping counter to allow 4 pings at min ping interval
		rapidPingCount = 4
		#Trigger next send now
		return activePingInterval
	elif rapidPingCount < 2:
		#Add 4 more pings at min ping interval
		rapidPingCount += 4
		#Let current cycle continue counting down
		return counter
	else:
		#Cancel rapid pings sequence
		rapidPingCount = 0
		activePingInterval = selectedPingInterval
		showBigMessage("Cancel")
		#Reset next send to full interval
		return 0
		
# Create lora object
lora = Rak811()

# Most of the setup should happen only once...
print("Setup")
# Update display message
showMessages("LoRa Mapper","IP:"+ip,"Send interval {}s".format(selectedPingInterval),"Setting Up LoRa Node")
lora.hard_reset()
lora.mode = Mode.LoRaWan
lora.band = "EU868"
lora.set_config(dev_addr=DEV_ADDR,
				apps_key=APPS_KEY,
				nwks_key=NWKS_KEY,
				adr="off")

# Join
showMessages("LoRa Mapper","IP:"+ip,"","Joining ABP")
print("Joining")
lora.join_abp()
lora.dr = 5
sf = 7
sent = 0

#Call these here to set short message globals used in status messages
showBtnAMode()
showBtnBMode()

print("Sending packets every {}seconds - Interrupt to cancel loop".format(selectedPingInterval))
print("You can send downlinks from the TTN console")

try:
	#Main endless map pinging loop inside error handler	
	sfOverride = False
	while True:
		#Reset menu mode on each send cycle
		menuMode = 4
		#Get actual SF from lora module for display in messages
		actualSF = 5 - lora.dr + 7
		if rapidPingCount > 0:
			print("Sending rapid mode {} SF={}".format(rapidPingCount,actualSF))
		else:
			print("Sending {} SF={}".format(sent+1,actualSF))
		showBigMessage("SF {}....".format(actualSF))
		# Cayenne lpp random value as analog
		lora.send(bytes.fromhex("0102{:04x}".format(randint(0, 0x7FFF))))
		sent +=1

		message = "SF{} Sent={}".format(actualSF,sent)
		showMessages("LoRa Mapper","IP:"+ip,message,"Waiting for reply...")
		while lora.nb_downlinks:
			message = lora.get_downlink()["data"].hex()
			print("Received " + message)
			showMidMessages("Received", message)
			sleep(10)
		
		#Reset SF if over-ridden
		if sfOverride:
			updateDr(sf)
			sfOverride = False
			
		#PingInterval can be over-ridden by buttons, so initialise here
		#Decrease as we just did a ping, then check again to set active interval
		if rapidPingCount > 0:
			rapidPingCount -= 1
		if rapidPingCount > 0:
			activePingInterval = minPingInterval
		else:
			activePingInterval = selectedPingInterval
		
		#Pause until next ping and check for inputs
		menuActive = 0
		i = 0
		while i < activePingInterval:
			i += 1

			#Check for inputs
			if button_A.value == False:
				#Check btn mode
				if btnAMode == 1:
					i = activateRapidPings(i)
				else:
					#Set temporary sf and trigger next send now
					tempSF = btnAMode + 5
					if 6 < tempSF < 13:
						#Set flag to indicate SF is over-ridden then over-ride and ping
						sfOverride = True
						updateDr(tempSF)
						i = activePingInterval
			elif button_B.value == False:
				#Check btn mode
				if btnBMode == 1:
					i = activateRapidPings(i)
				else:
					#Set temporary sf and trigger next send now
					tempSF = btnBMode + 5
					if 6 < tempSF < 13:
						#Set flag to indicate SF is over-ridden then over-ride and ping
						sfOverride = True
						updateDr(tempSF)
						i = activePingInterval
			elif button_C.value == False:
				#Trigger next send now
				i = activePingInterval
			elif button_D.value == False:
				while button_D.value == False:
					sleep(0.05)
				i -= (menuActiveTime - menuActive)
				menuActive = menuActiveTime
				pause = 0.05
				#Increment menu mode
				menuMode += 1
				if menuMode > 4:
					menuMode = 1
				if menuMode == 1:
					showMidMessages("Set SF","SF={}".format(sf))  
				elif menuMode == 2:
					showMidMessages("Set interval","Interval={}".format(selectedPingInterval))
				elif menuMode == 3:
					showBtnAMode()
				elif menuMode == 4:
					showBtnBMode()
			elif button_L.value == False:
				#Only allow change when menu active
				if menuActive > 0:
					while button_L.value == False:
						sleep(0.05)
					i -= (menuActiveTime - menuActive)
					menuActive = menuActiveTime
					pause = 0.05
					if menuMode == 1:
						#Decrease SF
						sf -= 1
						if sf < 7:
							sf = 7
						updateDr(sf)
					elif menuMode == 2:
						#Decrease ping interval by minPingInterval
						selectedPingInterval -= minPingInterval
						if selectedPingInterval < minPingInterval:
							selectedPingInterval = minPingInterval
						showSendInterval()
					elif menuMode == 3:
						#Decrease btnA mode
						btnAMode -= 1
						if btnAMode < 1:
							btnAMode = 1
						showBtnAMode()
					elif menuMode == 4:
						#Decrease btnB mode
						btnBMode -= 1
						if btnBMode < 1:
							btnBMode = 1
						showBtnBMode()
			elif button_R.value == False:
				#Only allow change when menu active
				if menuActive > 0:
					while button_R.value == False:
						sleep(0.05)
					i -= (menuActiveTime - menuActive)
					menuActive = menuActiveTime
					pause = 0.05
					if menuMode == 1:
						#Increase SF
						sf += 1
						if sf > 12:
							sf = 12
						updateDr(sf)
					elif menuMode == 2:
						#Increase ping interval by minPingInterval
						selectedPingInterval += minPingInterval
						showSendInterval()
					elif menuMode == 3:
						#Increase btnA mode
						btnAMode += 1
						if btnAMode > 7:
							btnAMode = 7
						showBtnAMode()
					elif menuMode == 4:
						#Increase btnB mode
						btnBMode += 1
						if btnBMode > 7:
							btnBMode = 7
						showBtnBMode()
			elif menuActive > 0:
				#Show menu settings messages and keep pause interval short
				menuActive -= 1
			else:
				#Menu input activity ended, revert to 1 second pause and std status message
				pause = 1
				if rapidPingCount > 0:
					#Rapid ping counter msg
					btnStatusMsg = "Rapid pings {}".format(rapidPingCount)
				else:
					#Standard status messages
					btnStatusMsg = "(" + btnAModeMsg + "      " + btnBModeMsg + ")"
				showMidMessages("SF{} Sent={}".format(sf,sent),"Next send {}s".format(activePingInterval-i),btnStatusMsg,rapidPingCount==0)
				
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
