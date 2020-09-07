from cyflash import bootload

import can
import time
import sys

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
	

def main():


	filename = sys.argv[1]
	baud = sys.argv[2]
	
	print("╔╗╔┌─┐─┐ ┬┌─┐┬ ┬┌─┐  ╦╦═╗╔═╗   ╔═╗┬  ┌─┐┌─┐┬ ┬┌─┐┬─┐")  
	print("║║║├┤ ┌┴┬┘└─┐│ │└─┐  ║╠╦╝╠═╝   ╠╣ │  ├─┤└─┐├─┤├┤ ├┬┘")  
	print("╝╚╝└─┘┴ └─└─┘└─┘└─┘  ╩╩╚═╩     ╚  ┴─┘┴ ┴└─┘┴ ┴└─┘┴└─")
	print("you shell now wait... \r\n")
	
	print("version 1.21\r\n")

	print("baudrate: " + baud + " bit/sec \r\n")
	
	
	args = 'cyflash_run.py '+ filename + ' --canbus=pcan --canbus_channel=PCAN_USBBUS1 --canbus_id=0x0ab --canbus_baudrate=' + baud
	args = args.split()
	sys.argv = args
	
	f = Flasher(baud)
	f.upload()


# Cal main entry point
main()