from cyflash import bootload

import can
import time
import sys

#####################################################################################
## Global Vars
#####################################################################################
_SN		= 0
_error	= False

#####################################################################################
## CAN Flasher class
#####################################################################################

class Flasher:
	def __init__(self,baud):
		print("Calling constructor")
		self.bus = "default"
		self.baud = int(baud)
		
	def send_reset(self):
		msg = can.Message(arbitration_id=0x180000DD,data=[0x8D, 0xC4, 0x55, 0x1B, 0xF0, 0x83, 0x67, 0xEA],extended_id=True)
		try:
			self.bus.send(msg)
			print("Send Reset.. !")
			#print("Message sent on {}".format(self.bus.channel_info))
		except can.CanError:
			print("Send Silence.. error")

	def send_wake(self):
		msg = can.Message(arbitration_id=0x180000EE,data=[0, 0, 0, 0, 0, 0, 0, 0],extended_id=True)
		try:
			self.bus.send(msg)
			print("Send wake..")
			#print("Message sent on {}".format(self.bus.channel_info))
		except can.CanError:
			print("Send wake.. error")
	
	def take_bus(self):
		self.bus = can.interface.Bus(bustype='pcan', channel='PCAN_USBBUS1', bitrate=self.baud)
		
	def release_bus(self):
		self.bus.shutdown()
		
	def upload(self):
		self.take_bus()
		
		for i in range(15):
			self.send_wake()
			time.sleep(1)


		self.send_reset()
		time.sleep(1)
		self.send_reset()
		time.sleep(1)
		
		self.release_bus()
		bootload.main()
		self.release_bus()

#####################################################################################
## Flash Upgrader: call flasher class with given params
#####################################################################################

def flash_upgrade():
	filename = sys.argv[1]
	baud	 = sys.argv[2]

	print("You shall now wait... \r\n")
	print("Version 1.22\r\n")
	print("Baudrate: " + baud + " bit/sec \r\n")
	
	args = 'cyflash_run.py '+ filename + ' --canbus=pcan --canbus_channel=PCAN_USBBUS1 --canbus_id=0x0ab --canbus_baudrate=' + baud
	args = args.split()
	sys.argv = args
	
	f = Flasher(baud)
	f.upload()
	time.sleep(0.5)

	print("----------------------\r\n")

#####################################################################################
## Fetch S/N: get serial number from the CAN messages
#####################################################################################

def fetch_sn():
	global _SN

	bus = can.interface.Bus(bustype='pcan', channel='PCAN_USBBUS1', bitrate=500000)

	try:
		print("Waiting for serial number...")

		msgCount = 0
		while True:
			message = bus.recv()
			if message.arbitration_id & 0xFFF0FFFF == 0x18000011:
				sn = message.data[0] << 24 | message.data[1] << 16 | message.data[2] << 8 | message.data[3];
				msgCount += 1

				if sn != 0:
					_SN = sn
					print("S/N Found: {} / {}".format(hex(sn), _SN))
					break
				
				if msgCount >= 3:
					print("NOTICE: S/N received as 0 - can't restore")
					_error = True
					break

	except can.CanError:
		_error = True
		print("CAN error")

	# release can
	bus.shutdown()
	time.sleep(0.5)

	print("----------------------\r\n")


#####################################################################################
## Sore S/N: send back the serial number
#####################################################################################

def restore_sn():
	global _SN

	if _SN == 0:
		print("No S/N detected - skiping S/N restoration", _SN)
		return

	bus = can.interface.Bus(bustype='pcan', channel='PCAN_USBBUS1', bitrate=500000)

	# CAN message to enter ATP mode, in order to change S/N
	msg_activate_atp = can.Message(arbitration_id=0x180F00DD, data=[0], is_extended_id=True)

	# CAN message to set the new S/N
	msg_set_sn = can.Message(arbitration_id=0x180F0011, data=_SN.to_bytes(4, byteorder='big'), is_extended_id=True)

	try:
		print("Entering ATP mode...")
		bus.send(msg_activate_atp)

		# wait for ATP mode ACK
		msgCount = 0
		while True:
			message = bus.recv()
			if message.arbitration_id & 0xFFF0FFFF == 0x180001FF:
				msgCount += 1

				if message.data[5] != 0:
					print("Got ATP mode ACK - proceeding")
					break
				
				if msgCount >= 3:
					print("Couldn't enter ATP mode")
					_error = True
					break

	except can.CanError:
		_error = True
		print("CAN error")

	print("")
	print("Restoring serial number...")
	bus.send(msg_set_sn)
	time.sleep(0.3)

	bus.send(msg_set_sn)
	time.sleep(0.3)

	# release can
	bus.shutdown()

	print("----------------------\r\n")

#####################################################################################
## Main
#####################################################################################

if __name__ == '__main__':
	print(" _   _                       _____ _____  _____    ______ _           _               ")  
	print("| \ | |                     |_   _|  __ \|  __ \  |  ____| |         | |              ")  
	print("|  \| | _____  ___   _ ___    | | | |__) | |__) | | |__  | | __ _ ___| |__   ___ _ __ ")
	print("| . ` |/ _ \ \/ | | | / __|   | | |  _  /|  ___/  |  __| | |/ _` / __| '_ \ / _ | '__|")
	print("| |\  |  __/>  <| |_| \__ \  _| |_| | \ \| |      | |    | | (_| \__ | | | |  __| |   ")
	print("|_| \_|\___/_/\_\\__,_| ___/ |_____|_|  \_|_|      |_|    |_|\__,_|___|_| |_|\___|_|   ")
	print("")

	fetch_sn()
	flash_upgrade()
	restore_sn()

	if _error == False:
		if _SN == 0:
			print("Flashing proceedure finished, S/N couldn't be restored")
		else:
			print("Flashing proceedure finished, S/N restored correctly")
	else:
		print("Something went wrong..")