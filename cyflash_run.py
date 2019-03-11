from cyflash import bootload

import can

print("SENDING RESET MSG")
bus = can.interface.Bus(bustype='pcan', channel='PCAN_USBBUS1', bitrate=250000)
msg = can.Message(arbitration_id=0x180000DD,data=[0, 0, 0, 0, 0, 0, 0, 0],extended_id=True)
try:
	bus.send(msg)
	print("Message sent on {}".format(bus.channel_info))
except can.CanError:
	print("Message NOT sent")

bus.shutdown();

# Call cyflash
bootload.main()


# bus = can.interface.Bus(bustype='pcan', channel='PCAN_USBBUS1', bitrate=250000)
msg = can.Message(arbitration_id=0x180000DD,data=[0, 0, 0, 0, 0, 0, 0, 0],extended_id=True)
try:
	bus.send(msg)
	print("Message sent on {}".format(bus.channel_info))
except can.CanError:
	print("Message NOT sent")