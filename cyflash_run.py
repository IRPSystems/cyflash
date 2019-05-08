from cyflash import bootload

import can
import time

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
		time.sleep(2)
		self.send_silence()
		time.sleep(2)
		self.send_silence()
		time.sleep(2)
		self.send_reset(bms_id)
		time.sleep(2)
		self.send_reset(bms_id)
		time.sleep(2)
		self.release_bus()
		bootload.main()
		self.release_bus()
	

def main():
	f = Flasher()
	for i in range(1,23):
		print("uploading " + str(i))
		f.upload(i%2 + 1)


# Cal main entry point
main()