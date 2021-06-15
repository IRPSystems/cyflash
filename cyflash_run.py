from cyflash import bootload

import can
import time
import sys
import pathlib
from datetime import datetime
import json

#####################################################################################
## Global Vars
#####################################################################################
_SN		= 0
_STATS	= {}
_error	= False

# for Grepow batteries there are 11 messages, Life batteries should get 15 messages
_AMOUNT_OF_STATS_MSGS = 11

#####################################################################################
## CAN Flasher class
#####################################################################################

class Flasher:
	def __init__(self,baud):
		#print("Calling constructor")
		self.bus = "default"
		self.baud = int(baud)
		
	def send_reset(self):
		msg = can.Message(arbitration_id=0x180000DD, data=[0x8D, 0xC4, 0x55, 0x1B, 0xF0, 0x83, 0x67, 0xEA], extended_id=True)
		try:
			self.bus.send(msg)
			print("Send Reset.. !")
		except can.CanError:
			print("Send reset.. error")

	def send_wake(self):
		msg = can.Message(arbitration_id=0x180000EE, data=[0], extended_id=True)
		try:
			self.bus.send(msg)
			print("Send wake..")
		except can.CanError:
			print("Send wake.. error")
	
	def take_bus(self):
		self.bus = can.interface.Bus(bustype='pcan', channel='PCAN_USBBUS1', bitrate=self.baud)
		
	def release_bus(self):
		self.bus.shutdown()
		
	def upload(self):
		for i in range(11):
			self.send_wake()
			time.sleep(1)

		self.send_reset()
		time.sleep(1)
		self.send_reset()
		time.sleep(1)
		
		self.release_bus()
		bootload.main()
		
		print("----------------------")

	#####################################################################################
	## Fetch S/N: get serial number from the CAN messages
	#####################################################################################

	def fetch_sn(self):
		global _SN, _error

		try:
			print("Waiting for serial number, this may take up to 30 seconds...")

			msgCount = 0
			while True:
				message = self.bus.recv()
				if message.arbitration_id & 0xFFF0FFFF == 0x18000011:
					sn = message.data[0] << 24 | message.data[1] << 16 | message.data[2] << 8 | message.data[3];
					msgCount += 1

					if sn != 0:
						_SN = sn
						print("S/N Found: {}".format(_SN))
						break
					
					if msgCount >= 3:
						print("NOTICE: S/N received as 0 - can't restore")
						_error = True
						break

		except can.CanError:
			_error = True
			print("CAN error - couldn't fetch S/N")

		print("----------------------")

	#####################################################################################
	## Sore S/N: send back the serial number
	#####################################################################################

	def restore_sn(self):
		global _SN, _error

		if _SN == 0:
			print("No S/N detected - skiping S/N restoration", _SN)
			return

		# CAN message to set the new S/N
		msg_set_sn = can.Message(arbitration_id=0x180F0011, data=_SN.to_bytes(4, byteorder='big'), is_extended_id=True)

		try:
			print("Restoring serial number...")
			self.bus.send(msg_set_sn)
			time.sleep(0.3)

			self.bus.send(msg_set_sn)
			time.sleep(0.3)

		except can.CanError:
			_error = True
			print("CAN error - couldn't restore S/N")

		print("----------------------")

	#####################################################################################
	## Fetch Stats: get all statistics before overwriting them
	#####################################################################################

	def fetch_stats(self):
		global _STATS, _AMOUNT_OF_STATS_MSGS, _error

		# CAN message to request statistics
		msg_request_stats = can.Message(arbitration_id=0x180000C0, data=[0], is_extended_id=True)

		try:
			print("Collecting statistics")
			self.bus.send(msg_request_stats)

			while True:
				message = self.bus.recv()
				# check if this is a statistics message
				if message.arbitration_id & 0xFFF0FFF0 == 0x180000C0:
					_STATS[(message.arbitration_id & 0x0000FFFF)] = message.data
					
					if len(_STATS) >= _AMOUNT_OF_STATS_MSGS:
						print("All stats collected")
						break

		except can.CanError:
			_error = True
			print("CAN error - couldn't fetch statistics")

		print("----------------------")

	#####################################################################################
	## Restore Stats: put back saved statistics in EEPROM
	#####################################################################################

	def restore_stats(self):
		global _STATS, _error

		try:
			print("Restoring statistics...")

			# order data by message IDs
			dict(sorted(_STATS.items()))

			for msg_id, msg_data in _STATS.items():
				print("Restoring msg ID: 0x{0:0{1}X}".format(msg_id, 4))
				msg_stats_restore = can.Message(arbitration_id=(msg_id | 0x180FFF00), data=msg_data, is_extended_id=True)
				self.bus.send(msg_stats_restore)
				time.sleep(0.3)

		except can.CanError:
			_error = True
			print("CAN error - couldn't restore statistics")

		print("----------------------")

	#####################################################################################
	## Enter ATP
	#####################################################################################

	def enter_atp(self):
		global _error

		# CAN message to enter ATP mode, in order to change S/N
		msg_activate_atp = can.Message(arbitration_id=0x180F00DD, data=[0], is_extended_id=True)

		try:
			print("Entering ATP mode...")
			time.sleep(0.5)
			self.bus.send(msg_activate_atp)

			# wait for ATP mode ACK
			msgCount = 0
			while True:
				message = self.bus.recv()
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
			print("CAN error - couldn't enter ATP mode")
			_error = True

		print("----------------------")

	#####################################################################################
	## Validate Stats
	#####################################################################################

	def validate_stats(self):
		global _STATS

		print("Validating statistics...")

		previous_stats = _STATS

		for i in range(0, 3):
			_STATS.clear()

			time.sleep(3)
			self.fetch_stats()
			time.sleep(0.5)

			if _STATS == previous_stats:
				break
			else:
				_STATS = previous_stats
				self.restore_stats()

		if _STATS != previous_stats:
			print("Not all statistics were restored!!")
		else:
			print("All statistics restored correctly")
	
		print("----------------------")
#################################### Flasher end ####################################

#####################################################################################
## Flash Upgrader: call flasher class with given params
#####################################################################################

def flash_upgrade():
	global filename, baud, _error
	
	args = 'cyflash_run.py '+ filename + ' --canbus=pcan --canbus_channel=PCAN_USBBUS1 --canbus_id=0x0ab --canbus_baudrate=' + baud
	args = args.split()
	sys.argv = args
	
	f = Flasher(baud)
	f.take_bus()

	# collect data from EEPROM
	f.fetch_sn()
	f.fetch_stats()

	# send the new FW image
	f.upload()
	f.release_bus()
	time.sleep(0.5)

	# enter ATP mode - should be sent only once
	f.take_bus()
	f.enter_atp()
	time.sleep(0.5)

	# restore collected data to the EEPROM, if all passed correctly
	if _error == False:
		print("Restoring data, please wait...")
		
		f.restore_sn()
		f.restore_stats()

		f.validate_stats()
	
	f.release_bus()

#####################################################################################
## Main
#####################################################################################

if __name__ == '__main__':
	filename = sys.argv[1]
	baud	 = sys.argv[2]

	print(" _   _                       _____ _____  _____    ______ _           _               ")  
	print("| \ | |                     |_   _|  __ \|  __ \  |  ____| |         | |              ")  
	print("|  \| | _____  ___   _ ___    | | | |__) | |__) | | |__  | | __ _ ___| |__   ___ _ __ ")
	print("| . ` |/ _ \ \/ | | | / __|   | | |  _  /|  ___/  |  __| | |/ _` / __| '_ \ / _ | '__|")
	print("| |\  |  __/>  <| |_| \__ \  _| |_| | \ \| |      | |    | | (_| \__ | | | |  __| |   ")
	print("|_| \_|\___/_/\_\\__,_| ___/ |_____|_|  \_|_|      |_|    |_|\__,_|___|_| |_|\___|_|   ")	# shifted to be displayed correctly
	print("")
	print("Version 1.22\r\n")
	print("You shall now wait... \r\n")
	print("Baudrate: " + baud + " bit/sec")
	print("----------------------\r\n")

	flash_upgrade()

	if _error == False:
		print("Flashing proceedure finished, {}".format( "S/N / stats couldn't be restored" if _SN == 0 else "S/N & stats restored correctly" ))
	else:
		# save log file
		time_now = datetime.now().strftime("%d%m%y_%H%M%S")
		log_name = "logs/{}_{}.json".format(_SN, time_now)
		log_stats = {}

		# convert byte array to int, so it can be saved as JSON
		for k, v in _STATS.items():
			log_stats[k] = int.from_bytes(v, byteorder='big', signed=False)

		log_data = {"sn": _SN, "stats": log_stats}

		pathlib.Path('logs').mkdir(parents=True, exist_ok=True) 
		log_file = open(log_name, "w")
		log_file.write(json.dumps(log_data))

		print("Something went wrong.. log saved into " + log_name)