# ttnmapper-node
Hardware project for mapping the things network using the PiSupply LoRa node pHAT.
This project uses a small monchrome OLED display from Adafruit (https://www.adafruit.com/product/3527) mounted on top of the PiSupply LoRa node pHAT (https://uk.pi-supply.com/products/iot-lora-node-phat-for-raspberry-pi) on a Raspberry Pi Zero. (It should work on any Raspberry Pi model which the LoRa node pHAT supports).

The software script is based on the example in the rak811 library:
https://github.com/AmedeeBulle/pyrak811/blob/master/examples/abp.py

This has been extended to use the OLED display to provide feedback, and keyboard input using a numerical keyboard to change settings while the mapper is running. I am using a Pimoroni Keybow keyboard (https://shop.pimoroni.com/products/keybow) in the default numeric keyboard mapping.

This project does not include GPS data from the Pi currently (this would require a GPS module). Instead a mobile device running the ttnmapper app is required to be running alongside the Pi to provide GPS location data to The Things Network when data is successfully recieved by a gateway on the network.

## Hardware build
I used a Raspberry Pi Zero W with the official Raspberry Pi Foundation case. The PiSupply LoRa node pHAT plugs onto the GPIO header and the Adafruit OLED display simply plugs in on top of the header pins which protrude through the pHAT. To provide flexibility in positioning the antenna (and to prevent it shorting and exposed contacts on the pHAT) I attached it using a large lump of blu-tak.

![alt text](https://github.com/Footleg/ttnmapper-node/raw/master/LoRa%20mapper%20hardware.jpg "TTN Mapper Hardware Photo")

## Installation
The code requires a couple of libraries to be installed using the pip3 utility in order to run.
You may need to install pip3 using the following commands:
> sudo apt-get update
> sudo apt-get install python3-pip

Now install the rak811 library using the command:
> sudo pip3 install rak811

If you already have the rak811 library installed you can upgrade it to the latest version using the command:
> sudo pip3 install --upgrade rak811

You also need to install the keyboard library for the keyboard input:
> sudo pip3 install keyboard

Next clone this git repo onto your Pi:
git clone https://github.com/footleg/ttnmapper-node.git

Next open the ttn_secrets.py file in the ttnmapper-node directory and fill in the correct secret keys for your ttn application and device. These can all be read from the ttn-console https://console.thethingsnetwork.org/ for your application. Note you do not need the APP_KEY for this application. You can find all the other information you need on the 'applications/<your app name>/devices/<your device name>/Overview' page if you drill down on the console webpage.

Finally you will need to copy an ARIAL.TTF TrueType font file into the application directory before it will run.

## Running the mapper
To run the mapper to test it is all working, you just need to run the loramapperkbd.py python3 script with sudo rights (required because the keyboard input library requires them):
> sudo python3 loramapperkbd.py


## Auto-run on boot
TBC
