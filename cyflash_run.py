from cyflash import bootload

import serial
import sys

class Flasher:

	def __init__(self, baud, com):
		print("Calling constructor")
		self.ser = serial.Serial()
		self.ser.port = com
		self.ser.baudrate = int(baud)
		
		self.ser.open()

	def send_bootload_enter(self):
		self.ser.write(b'\x60\x00\x00\x00\x59\xD2')
		print("Entering bootloader..")
	
	def close_connection(self):
		self.ser.close()
		print("Finished bootloading")
	
	def upload(self):
		self.send_bootload_enter()
		
		self.close_connection()
		bootload.main()
		

def main():
	filename = sys.argv[1]
	baud = sys.argv[2]
	com = sys.argv[3]
	
	print("╔╗╔┌─┐─┐ ┬┌─┐┬ ┬┌─┐  ╦╦═╗╔═╗   ╔═╗┬  ┌─┐┌─┐┬ ┬┌─┐┬─┐")  
	print("║║║├┤ ┌┴┬┘└─┐│ │└─┐  ║╠╦╝╠═╝   ╠╣ │  ├─┤└─┐├─┤├┤ ├┬┘")  
	print("╝╚╝└─┘┴ └─└─┘└─┘└─┘  ╩╩╚═╩     ╚  ┴─┘┴ ┴└─┘┴ ┴└─┘┴└─")
	print("you shell now wait... \r\n")
	
	print("version 1.21\r\n")

	print("baudrate: " + baud + " bit/sec \r\n")
	
	
	args = 'cyflash_run.py '+ filename + ' --serial ' + com + ' --serial_baudrate=' + baud
	args = args.split()
	sys.argv = args
	
	f = Flasher(baud, com)
	f.upload()


# Call main entry point
main()
