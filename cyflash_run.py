from cyflash import bootload

import can
import time
import sys

class Flasher:

	def __init__(self):
		print("Calling constructor")
		self.bus = "default"
		
	def send_reset(self,bms_id):
		msg = can.Message(arbitration_id=0x180000DD,data=[bms_id, 0, 0, 0, 0, 0, 0, 0],extended_id=True)
		try:
			self.bus.send(msg)
			print("Send Reset.. to " + str(bms_id))
			#print("Message sent on {}".format(self.bus.channel_info))
		except can.CanError:
			print("Send Silence.. error")

	def send_silence(self):
		msg = can.Message(arbitration_id=0x180000DF,data=[0, 0, 0, 0, 0, 0, 0, 0],extended_id=True)
		try:
			self.bus.send(msg)
			print("Send Silence..")
			#print("Message sent on {}".format(self.bus.channel_info))
		except can.CanError:
			print("Send Silence.. error")
	
	def take_bus(self):
		self.bus = can.interface.Bus(bustype='pcan', channel='PCAN_USBBUS1', bitrate=1000000)
		
	def release_bus(self):
		self.bus.shutdown()
		
	def upload(self, bms_id):
		self.take_bus()
		time.sleep(1)
		self.send_silence()
		self.send_silence()
		time.sleep(1)
		self.send_silence()
		self.send_reset(bms_id)
		self.send_reset(bms_id)
		time.sleep(1)
		self.send_reset(bms_id)
		time.sleep(1)
		self.release_bus()
		bootload.main()
		self.release_bus()
	

def main():

	print (sys.argv[0])
	filename = sys.argv[1]
	start_bms = int(sys.argv[2])
	end_bms = int(sys.argv[3])
	

	if (start_bms > end_bms):
		print("Bad input bms ids start id cannot be larger then stop id")
		sys.exit()
		
	print("╔╗╔┌─┐─┐ ┬┌─┐┬ ┬┌─┐  ╦╦═╗╔═╗  ╔═╗┬  ┬┌─┐┬┌─┐┌┬┐┬┌─┐┌┐┌  ╔═╗┬  ┌─┐┌─┐┬ ┬┌─┐┬─┐")  
	print("║║║├┤ ┌┴┬┘└─┐│ │└─┐  ║╠╦╝╠═╝  ║╣ └┐┌┘├┤ │├─┤ │ ││ ││││  ╠╣ │  ├─┤└─┐├─┤├┤ ├┬┘")  
	print("╝╚╝└─┘┴ └─└─┘└─┘└─┘  ╩╩╚═╩    ╚═╝ └┘ └─┘┴┴ ┴ ┴ ┴└─┘┘└┘  ╚  ┴─┘┴ ┴└─┘┴ ┴└─┘┴└─")
	print("version 1.0\r\n")
	print("******************************************************")
	print("uploading ... " + filename)
	print("Uploading bms id from ",start_bms," to ",end_bms," ...")
	print("******************************************************")
	
	args = 'cyflash_run.py '+ filename + ' --canbus=pcan --canbus_channel=PCAN_USBBUS1 --canbus_id=0x0ab --canbus_baudrate=1000000'
	args = args.split()
	sys.argv = args
	
	f = Flasher()
	for i in range(start_bms,end_bms + 1):
		print("uploading " + str(i))
		f.upload(i)


# Cal main entry point
main()