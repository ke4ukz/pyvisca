import serial
import threading
from time import sleep, time
from enum import IntEnum
from struct import pack, unpack

class Camera:
	"""Sony VISCA camera communications protocol over a serial port"""

	class PictureEffects(IntEnum):
		NONE = 0x00
		NEGATIVE_ART = 0x02
		BLACK_AND_WHITE = 0x04

	class WhiteBalance(IntEnum):
		AUTO = 0x00
		INDOOR = 0x01
		OUTDOOR = 0x02
		ONEPUSH = 0x03
		MANUAL = 0x05

	class AutoExposure(IntEnum):
		AUTO = 0x00
		MANUAL = 0x03
		SHUTTER_PRIORITY = 0x0A
		IRIS_PRIORITY = 0x0B
		BRIGHT = 0x0D

	# All of these commands DO NOT include the address byte
	# because it will be added later when the command is sent
	POWERON = [0x01, 0x04, 0x00, 0x02, 0xFF]
	POWEROFF = [0x01, 0x04, 0x00, 0x03, 0xFF]
	CANCELCOMMAND = [0x21, 0xFF]
	ZOOMIN = [0x01, 0x04, 0x07, 0x02, 0xFF]
	ZOOMOUT = [0x01, 0x04, 0x07, 0x03, 0xFF]
	ZOOMSTOP = [0x01, 0x04, 0x07, 0x00, 0xFF]
	FOCUSSTOP = [0x01, 0x04, 0x08, 0x00, 0xFF]
	FOCUSFAR = [0x01, 0x04, 0x08, 0x02, 0xFF]
	FOCUSNEAR = [0x01, 0x04, 0x08, 0x03, 0xFF]
	FOCUSINF = [0x01, 0x04, 0x18, 0x02, 0xFF]
	ONEPUSHAF = [0x01, 0x04, 0x18, 0x01, 0xFF]
	AFON = [0x01, 0x04, 0x38, 0x02, 0xFF]
	AFOFF = [0x01, 0x04, 0x38, 0x03, 0xFF]
	GOHOME = [0x01, 0x06, 0x04, 0xFF]
	MOUNTUP = [0x01, 0x04, 0xA4, 0x02, 0xFF]
	MOUNTDOWN = [0x01, 0x04, 0xA4, 0x04, 0xFF]
	FLIPON = [0x01, 0x04, 0x66, 0x02, 0xFF]
	FLIPOFF = [0x01, 0x04, 0x66, 0x03, 0xFF]
	REVERSEON = [0x01, 0x04, 0x61, 0x02, 0xFF]
	REVERSEOFF = [0x01, 0x04, 0x61, 0x03, 0xFF]
	RESET = [0x01, 0x06, 0x05, 0xFF]
	FREEZEON = [0x01, 0x04, 0x62, 0x02, 0xFF]
	FREEZEOFF = [0x01, 0x04, 0x62, 0x03, 0xFF]
	PRESETFREEZEON = [0x01, 0x04, 0x62, 0x22, 0xFF]
	PRESETFREEZEOFF = [0x01, 0x04, 0x62, 0x23, 0xFF]
	MOVESTOP = [0x01, 0x06, 0x01, 0x01, 0x01, 0x03, 0x03, 0xFF]
	TALLYON = [0x01, 0x7E, 0x01, 0x0A, 0x00, 0x02, 0xFF]
	TALLYOFF = [0x01, 0x7E, 0x01, 0x0A, 0x00, 0x03, 0xFF]
	WBONEPUSHTRIGGER = [0x01, 0x04, 0x10, 0x05]
	REDGAINRESET = [0x01, 0x04, 0x03, 0x00, 0xFF]
	REDGAINUP = [0x01, 0x04, 0x03, 0x02, 0xFF]
	REDGAINDOWN = [0x01, 0x04, 0x03, 0x03, 0xFF]
	BLUEGAINRESET = [0x01, 0x04, 0x04, 0x00, 0xFF]
	BLUEGAINUP = [0x01, 0x04, 0x04, 0x02, 0xFF]
	BLUEGAINDOWN = [0x01, 0x04, 0x04, 0x03, 0xFF]
	MENUON = [0x01, 0x06, 0x06, 0x02, 0xFF]
	MENUOFF = [0x01, 0x06, 0x06, 0x03, 0xFF]
	MENUBACK = [0x01, 0x06, 0x06, 0x10, 0xFF]
	MENUOK = [0x01, 0x7E, 0x01, 0x02, 0x00, 0x01, 0xFF]
	WIDEON = [0x01, 0x04, 0x60, 0x02, 0xFF]
	WIDEOFF = [0x01, 0x04, 0x60, 0x00, 0xFF]
	SHUTTERUP = [0x01, 0x04, 0x0A, 0x02, 0xFF]
	SHUTTERDOWN = [0x01, 0x04, 0x0A, 0x03, 0xFF]
	SHUTTERRESET = [0x01, 0x04, 0x0A, 0x00, 0xFF]
	IRISUP = [0x01, 0x04, 0x0B, 0x02, 0xFF]
	IRISDOWN = [0x01, 0x04, 0x0B, 0x03, 0xFF]
	IRISRESET = [0x01, 0x04, 0x0B, 0x00, 0xFF]
	GAINUP = [0x01, 0x04, 0x0C, 0x02, 0xFF]
	GAINDOWN = [0x01, 0x04, 0x0C, 0x03, 0xFF]
	GAINRESET = [0x01, 0x04, 0x0C, 0x00, 0xFF]
	BRIGHTNESSUP = [0x01, 0x04, 0x0D, 0x02, 0xFF]
	BRIGHTNESSDOWN = [0x01, 0x04, 0x0D, 0x03, 0xFF]
	BRIGHTNESSRESET = [0x01, 0x04, 0x0D, 0x00, 0xFF]
	EXPUP = [0x01, 0x04, 0x0E, 0x02, 0xFF]
	EXPDOWN = [0x01, 0x04, 0x0E, 0x03, 0xFF]
	EXPRESET = [0x01, 0x04, 0x0E, 0x00, 0xFF]
	APERTUREUP = [0x01, 0x04, 0x02, 0x02, 0xFF]
	APERTUREDOWN = [0x01, 0x04, 0x02, 0x03, 0xFF]
	APERTURERESET = [0x01, 0x04, 0x02, 0x00, 0xFF]
	BACKLIGHTON = [0x01, 0x04, 0x33, 0x02, 0xFF]
	BACKLIGHTOFF = [0x01, 0x04, 0x33, 0x03, 0xFF]
	INQ_POWER = [0x09, 0x04, 0x00, 0xFF]
	INQ_AUTOFOCUS = [0x09, 0x04, 0x38, 0xFF]
	INQ_PICTUREEFFECT = [0x09, 0x04, 0x63, 0xFF]
	INQ_PRESET = [0x09, 0x04, 0x3F, 0xFF]
	INQ_TALLY = [0x09, 0x7E, 0x01, 0x0A, 0xFF]
	INQ_WHITEBALANCE = [0x09, 0x04, 0x35, 0xFF]
	INQ_AEMODE = [0x09, 0x04, 0x39, 0xFF]
	INQ_IMAGEFLIP = [0x09, 0x04, 0x66, 0xFF]
	INQ_PANREVERSE = [0x09, 0x7E, 0x01, 0x06, 0xFF]
	INQ_TILTREVERSE = [0x09, 0x7E, 0x01, 0x09, 0xFF]
	INQ_PANTILT = [0x09, 0x06, 0x12, 0xFF]
	INQ_VERSION = [0x09, 0x00, 0x02, 0xFF]
	INQ_REDGAIN = [0x09, 0x04, 0x43, 0xFF]
	INQ_BLUEGAIN = [0x09, 0x04, 0x44, 0xFF]
	INQ_WIDEMODE = [0x09, 0x04, 0x60, 0xFF]
	INQ_SHUTTER = [0x09, 0x04, 0x4A, 0xFF]
	INQ_IRIS = [0x09, 0x04, 0x4B, 0xFF]
	INQ_GAIN = [0x09, 0x04, 0x4C, 0xFF]
	INQ_BRIGHTNESS = [0x09, 0x0D, 0x4C, 0xFF]
	INQ_EXP = [0x09, 0x04, 0x4E, 0xFF]
	INQ_APERTURE = [0x09, 0x04, 0x42, 0xFF]
	INQ_BACKLIGHT = [0x09, 0x04, 0x33, 0xFF]
	
	def _dp(self, text):
		"""Print if in debug mode"""
		if (self._debugmode):
			print(text)

	def __init__(self, port, baudrate, address=1, pan_bytes=4, tilt_bytes=4, debugmode=False):
		self._serial = serial.Serial(port=port, baudrate=baudrate, timeout=0)
		self._debugmode = debugmode
		self.camera_address = address
		self.pan_bytes = pan_bytes
		self.tilt_bytes = tilt_bytes

	def _splitnibbles(self, v, n=4):
		"""Splits an integer value into a list of individual nibbles"""
		r = []
		for i in range(0, n):
			r = [(v >> (4 * i) & 0x0f)] + r
		return r

	def _combinenibbles(self, v):
		"""Combines a list of individual nibbles (0x00 to 0x0f) to an integer"""
		r = 0
		n = len(v)
		if (n == 0):
			return 0
		for i in range(0, n):
			c = v[i]
			m = 16 ** (n - i - 1)
			r += (c * m)
		return r
	def _map(self, x, in_min, in_max, out_min, out_max):
		"""Maps a value within a range to the same position in a different range"""
		return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

	def _sendcommand(self, command):
		"""Send the given command to a camera using the selected address"""
		cmd = bytes([0x80 + self.camera_address] + command)
		self._dp("COMMAND: " + str([hex(c) for c in list(cmd)]))
		self._serial.write(cmd)
		sleep(0.1)

	def _getresponse(self, address=None, timeout=2):
		"""Waits for a response from a camera"""
		if (address == None): address = self.camera_address
		starttime = time()
		while(time() - starttime < timeout):
			if (self._serial.in_waiting > 0):
				readbytes = self._serial.read(self._serial.in_waiting)
				inputs = readbytes.split(bytes([0xFF]))
				for input in inputs:
					if (len(input) > 0):
						retaddress = (list(input)[:1][0] - 0x80) >> 4
						if (retaddress == address): #ignore responses from other cameras
							response = list(input)[1:]
							if (len(response) > 1):
								if (response[0] == 0x50): #only return actual inquiry responses
									# valid response
									return response
								elif (response[0:1] == [0x60, 0x02]):
									# command syntax error
									self._dp("Syntax error")
									return None
								elif (response[0:1] == [0x61, 0x41]):
									# command not executable
									self._dp("Command not executable")
									return None
			else:
				sleep(0.1)
		self._dp("Timeout waiting for response")
		return None # No response for this camera in the timeout period
	
	@property
	def debug_mode(self):
		return self._debugmode
	@debug_mode.setter
	def debug_mode(self, mode):
		self._debugmode = mode

	def zoom_in(self, speed=4):
		self._dp("Zooming in")
		self._sendcommand([0x01, 0x04, 0x07, 0x20 + speed, 0xFF])
		#self._sendcommand(self.ZOOMIN)

		
	def zoom_out(self, speed=4):
		self._dp("Zooming out")
		self._sendcommand([0x01, 0x04, 0x07, 0x30 + speed, 0xFF])
		#self._sendcommand(self.ZOOMOUT)

	def zoom_stop(self):
		self._dp("Stopping zoom")
		self._sendcommand(self.ZOOMSTOP)

	def zoom_to(self, percent):
		amt = int(0x4000 * percent)
		b = self._splitnibbles(amt, 4)
		self._dp("Zooming to " + str(100 * percent) + " percent (" + "0x{:04x}".format(amt) + ")")
		self._sendcommand([0x01, 0x04, 0x47, b[0], b[1], b[2], b[3], 0xFF])

	def focus_near(self):
		self._dp("Focusing near")
		#self._sendcommand([0x01, 0x04, 0x08, 0x30+self.focus_speed, 0xFF])
		self._sendcommand(self.FOCUSNEAR)

	def focus_far(self):
		self._dp("Focusing far")
		#self._sendcommand([0x01, 0x04, 0x08, 0x20+self.focus_speed, 0xFF])
		self._sendcommand(self.FOCUSFAR)

	def focus_stop(self):
		self._dp("Stopping focus")
		self._sendcommand(self.FOCUSSTOP)

	def focus_auto(self):
		self._dp("Autofocus")
		self._sendcommand(self.ONEPUSHAF)

	def focus_infinity(self):
		self._dp("Focusing to infinity")
		self._sendcommand(self.FOCUSINF)
		
	def focus_to(self, percent):
		amt = int(0x4000 * percent)
		b = self._splitnibbles(amt, 4)
		self._dp("Focusing to " + str(100 * percent) + " percent (" + "0x{:04x}".format(amt) + ")")
		self._sendcommand([0x01, 0x04, 0x48, b[0], b[1], b[2], b[3], 0xFF])

	def zoomfocus_to(self, zoom, focus):
		zamt = int(0x4000 * zoom)
		famt = int(0x4000 * focus)
		b1 = self._splitnibbles(zamt)
		b2 = self._splitnibbles(famt)
		self._dp("Zooming to " + str(100 * zoom) + " percent (" + "0x{:04x}".format(zamt) + ")")
		self._dp("Focusing to " + str(100 * focus) + " percent (" + "0x{:04x}".format(famt) + ")")
		self._sendcommand([0x01, 0x04, 0x47, b1[1], b1[1], b1[2], b1[3], b2[0], b2[1], b2[2], b2[3], 0xFF])

	def move_stop(self):
		self._dp("Stopping movement")
		self._sendcommand(self.MOVESTOP)

	def move_left(self, speed=0x07):
		self._dp("Moving left")
		self._sendcommand([0x01, 0x06, 0x01, speed, speed, 0x01, 0x03, 0xFF])

	def move_right(self, speed=0x07):
		self._dp("Moving right")
		self._sendcommand([0x01, 0x06, 0x01, speed, speed, 0x02, 0x03, 0xFF])

	def move_up(self, speed=0x07):
		self._dp("Moving up")
		self._sendcommand([0x01, 0x06, 0x01, speed, speed, 0x03, 0x01, 0xFF])

	def move_down(self, speed=0x07):
		self._dp("Moving down")
		self._sendcommand([0x01, 0x06, 0x01, speed, speed, 0x03, 0x02, 0xFF])

	def move_upleft(self, speed=0x07):
		self._dp("Moving up-left")
		self._sendcommand([0x01, 0x06, 0x01, speed, speed, 0x01, 0x01, 0xFF])

	def move_upright(self, speed=0x07):
		self._dp("Moving up-right")
		self._sendcommand([0x01, 0x06, 0x01, speed, speed, 0x02, 0x01, 0xFF])

	def move_downleft(self, speed=0x07):
		self._dp("Moving down-left")
		self._sendcommand([0x01, 0x06, 0x01, speed, speed, 0x01, 0x02, 0xFF])

	def move_downright(self, speed=0x07):
		self._dp("Moving down-right")
		self._sendcommand([0x01, 0x06, 0x01, speed, speed, 0x02, 0x02, 0xFF])

	def move_to(self, speed=0x07, pan=0, tilt=0):
		self._dp("Moving to " + hex(pan) + " by " + hex(tilt))
		self._sendcommand([0x01, 0x06, 0x02, speed, speed] + self._splitnibbles(pan, self.pan_bytes) + self._splitnibbles(tilt, self.tilt_bytes) + [0xff])

	def get_pantilt(self):
		pantilt = {"pan":0, "tilt":0}
		self._sendcommand(self.INQ_PANTILT)
		ret = self._getresponse()
		if (ret != None):
			if (len(ret) > 0):
				if (ret[0] == 0x50):
					pan = ret[1:self.pan_bytes+1]
					tilt = ret[self.pan_bytes+1:self.pan_bytes+1+self.tilt_bytes]                
					pantilt["pan"] = self._combinenibbles(pan)
					pantilt["tilt"] = self._combinenibbles(tilt)
		return pantilt

	@property
	def picture_effect(self):
		self._sendcommand(self.INQ_PICTUREEFFECT)
		ret = self._getresponse()
		if (ret == [0x50, 0x00]):
			return self.PictureEffects.NONE
		elif (ret == [0x50, 0x02]):
			return self.PictureEffects.NEGATIVE_ART
		elif (ret == [0x50, 0x04]):
			return self.PictureEffects.BLACK_AND_WHITE
		else:
			return 0

	@picture_effect.setter
	def picture_effect(self, effect):
		self._dp("Setting picture effect to " + str(effect))
		self._sendcommand([0x01, 0x04, 0x63, int(effect), 0xFF])

	@property
	def white_balance(self):
		self._sendcommand(self.INQ_WHITEBALANCE)
		ret = self._getresponse()
		if (ret == [0x50, 0x00]):
			return self.WhiteBalance.AUTO
		elif (ret == [0x50, 0x01]):
			return self.WhiteBalance.INDOOR
		elif (ret == [0x50, 0x02]):
			return self.WhiteBalance.OUTDOOR
		elif (ret == [0x50, 0x03]):
			return self.WhiteBalance.ONEPUSH
		elif (ret == [0x50, 0x05]):
			return self.WhiteBalance.MANUAL
		else:
			return 0

	@white_balance.setter
	def white_balance(self, mode):
		self._dp("Setting white balance to " + str(mode))
		self._sendcommand([0x01, 0x04, 0x35, mode, 0xFF])
		if (mode == self.WhiteBalance.ONEPUSH):
			sleep(0.1)
			self._sendcommand(self.WBONEPUSHTRIGGER)

	@property
	def red_gain(self):
		self._sendcommand(self.INQ_REDGAIN)
		ret = self._getresponse()
		if (ret == None):
			return 0
		if (len(ret) > 0):
			if (ret[0] == 0x50):
				return self._combinenibbles(ret[3:5])
		return 0
		
	@red_gain.setter
	def red_gain(self, red):
		self._sendcommand([0x01, 0x04, 0x43, 0x00, 0x00] + self._splitnibbles(red, 2) + [0xFF])

	def reset_red_gain(self):
		self._sendcommand(self.REDGAINRESET)

	def increase_red_gain(self):
		self._sendcommand(self.REDGAINUP)

	def decrease_red_gain(self):
		self._sendcommand(self.REDGAINDOWN)

	@property
	def blue_gain(self):
		self._sendcommand(self.INQ_BLUEGAIN)
		ret = self._getresponse()
		if (ret == None):
			return 0
		if (len(ret) > 0):
			if (ret[0] == 0x50):
				return self._combinenibbles(ret[3:5])
		return 0
		
	@blue_gain.setter
	def blue_gain(self, blue):
		self._sendcommand([0x01, 0x04, 0x44, 0x00, 0x00] + self._splitnibbles(blue, 2) + [0xFF])

	def reset_blue_gain(self):
		self._sendcommand(self.BLUEGAINRESET)

	def increase_blue_gain(self):
		self._sendcommand(self.BLUEGAINUP)

	def decrease_blue_gain(self):
		self._sendcommand(self.BLUEGAINDOWN)

	@property
	def ae_mode(self):
		self._sendcommand(self.INQ_AEMODE)
		ret = self._getresponse()
		if (ret == [0x50, 0x00]):
			return self.AutoExposure.AUTO
		elif (ret == [0x50, 0x03]):
			return self.AutoExposure.MANUAL
		elif (ret == [0x50, 0x0A]):
			return self.AutoExposure.SHUTTER_PRIORITY
		elif (ret == [0x50, 0x0B]):
			return self.AutoExposure.IRIS_PRIORITY
		elif (ret == [0x50, 0x0D]):
			return self.AutoExposure.BRIGHT
		else:
			return 0

	@ae_mode.setter
	def ae_mode(self, mode):
		self._dp("Setting autoexposure to " + str(mode))
		self._sendcommand([0x01, 0x04, 0x39, mode, 0xFF])

	def title(self, title="", blink=False):
		self._dp("Setting title to " + title)
		#title clear
		self._sendcommand([0x01, 0x7E, 0x01, 0x13, 0x00, 0xFF])
		sleep(0.1)
		
		N = 10
		P = 0
		hPos = 0x00
		vPos = 0x00
		blinking = 0x01 if blink else 0x00
		t1 = list(bytes(title[:10], "ascii"))
		t2 = list(bytes(title[10:20], "ascii"))
		t1 = (t1 + N * [P])[:N]
		t2 = (t2 + N * [P])[:N]
		
		self._sendcommand([0x01, 0x7E, 0x01, 0x10, hPos, vPos, blinking, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF])
		sleep(0.1)
		self._sendcommand([0x01, 0x7E, 0x01, 0x11] + t1 + [0xFF])
		sleep(0.1)
		self._sendcommand([0x01, 0x7E, 0x01, 0x12] + t2 + [0xFF])
		sleep(0.1)
		#title on
		self._sendcommand([0x01, 0x7E, 0x01, 0x13, 0x02, 0xFF])

	def command(self, command):
		"""Send a custom command to the camera (do not include the camera address byte)"""
		self._sendcommand(command)
		
	def home(self):
		"""Return the camera to its home position"""
		self._dp("Going home")
		self._sendcommand(self.GOHOME)

	def reset(self):
		"""Reset the camera (as if powering off and on again)"""
		self._dp("Resetting camera")
		self._sendcommand(self.RESET)

	def video_system(self, videosystem):
		print("Setting video system to " + str(videosystem))
		self._sendcommand([0x01, 0x06, 0x35, 0x00, videosystem, 0xFF])

	@property
	def freeze(self):
		return None # can't get this property

	@freeze.setter
	def freeze(self, freeze=True):
		if (freeze):
			self._dp("Freezing image")
			self._sendcommand(self.FREEZEON)
		else:
			self._dp("Unfreezing image")
			self._sendcommand(self.FREEZEOFF)

	@property
	def preset_freeze(self):
		return None # can't get this property

	@preset_freeze.setter
	def preset_freeze(self, freeze=True):
		if (freeze):
			self._sendcommand(self.PRESETFREEZEON)
		else:
			self._sendcommand(self.PRESETFREEZEOFF)    

	@property
	def pan_reverse(self):
		self._sendcommand(self.INQ_PANREVERSE)
		ret = self._getresponse()
		if (ret == [0x50, 0x01]):
			return True
		elif (ret == [0x50, 0x00]):
			return False
		else:
			return None

	@pan_reverse.setter
	def pan_reverse(self, reverse=True):
		if (reverse):
			self._sendcommand([0x01, 0x7E, 0x01, 0x06, 0x00, 0x01, 0xFF])
		else:
			self._sendcommand([0x01, 0x7E, 0x01, 0x06, 0x00, 0x00, 0xFF])

	@property
	def tilt_reverse(self):
		self._sendcommand(self.INQ_TILTREVERSE)
		ret = self._getresponse()
		if (ret == [0x50, 0x01]):
			return True
		elif (ret == [0x50, 0x00]):
			return False
		else:
			return None

	@tilt_reverse.setter
	def tilt_reverse(self, reverse=True):
		if (reverse):
			self._sendcommand([0x01, 0x7E, 0x01, 0x09, 0x00, 0x01, 0xFF])
		else:
			self._sendcommand([0x01, 0x7E, 0x01, 0x09, 0x00, 0x00, 0xFF])

	@property
	def power_on(self):
		self._sendcommand(self.INQ_POWER)
		ret = self._getresponse()
		if (ret == [0x50, 0x02]):
			return True
		elif (ret == [0x50, 0x03]):
			return False
		else:
			return None

	@power_on.setter
	def power_on(self, on=True):
		if (on):
			self._dp("Powering camera on")
			self._sendcommand(self.POWERON)
		else:
			self._dp("Powering camera off")
			self._sendcommand(self.POWEROFF)

	@property
	def autofocus(self):
		self._sendcommand(self.INQ_AUTOFOCUS)
		ret = self._getresponse()
		if (ret == [0x50, 0x02]):
			return True
		elif (ret == [0x50, 0x03]):
			return False
		else:
			return None        

	@autofocus.setter
	def autofocus(self, af=True):
		if (af):
			self._dp("Autofocus on")
			self._sendcommand(self.AFON)
		else:
			self._dp("Autofocus off")
			self._sendcommand(self.AFOFF)
			
	@property
	def image_flip(self):
		self._sendcommand(self.INQ_IMAGEFLIP)
		ret = self._getresponse()
		if (ret == [0x50, 0x02]):
			return True
		elif (ret == [0x50, 0x03]):
			return False
		else:
			return None
		
	@image_flip.setter
	def image_flip(self, flip=True):
		if (flip):
			self._dp("Flipping image")
			self._sendcommand(self.FLIPON)
		else:
			self._dp("Unflipping image")
			self._sendcommand(self.FLIPOFF)

	def image_reverse(self, reverse=True):
		if (reverse):
			self._dp("Reversing image")
			self._sendcommand(self.REVERSEON)
		else:
			self._dp("Unreversing image")
			self._sendcommand(self.REVERSEOFF)

	@property
	def preset(self):
		self._sendcommand(self.INQ_PRESET)
		ret = self._getresponse()
		if (ret != None) and (len(ret) > 1):
			return ret[1]
		else:
			return 0

	@preset.setter
	def preset(self, slot):
		self._sendcommand([0x01, 0x04, 0x3F, 0x02, slot, 0xFF])

	def store_preset(self, slot):
		self._sendcommand([0x01, 0x04, 0x3F, 0x01, slot, 0xFF])
		
	def clear_preset(self, slot):
		self._sendcommand([0x01, 0x04, 0x3F, 0x00, slot, 0xFF])

	@property
	def tally_on(self):
		self._sendcommand(self.INQ_TALLY)
		ret = self._getresponse()
		if (ret == [0x50, 0x02]):
			return True
		elif (ret == [0x50, 0x03]):
			return False
		else:
			return None

	@tally_on.setter
	def tally_on(self, on=True):
		if (on):
			self._sendcommand(self.TALLYON)
		else:
			self._sendcommand(self.TALLYOFF)

	def getVersionInfo(self):
		version = {"vendor":None, "model":None, "rom":None, "sockets":0}
		self._sendcommand(self.INQ_VERSION)
		ret = self._getresponse()
		if (ret != None):
			if (len(ret) > 0):
				if (ret[0] == 0x50):
					version = {}
					version["vendor"] = self._combinenibbles(ret[1:3])
					version["model"] = self._combinenibbles(ret[3:5])
					version["rom"] = self._combinenibbles(ret[5:7])
					version["sockets"] = ret[7]
		return version

	def menu_show(self):
		self._sendcommand(self.MENUON)
		
	def menu_hide(self):
		self._sendcommand(self.MENUOFF)
		
	def menu_back(self):
		self._sendcommand(self.MENUBACK)
		
	def menu_ok(self):
		self._sendcommand(self.MENUOK)

	@property
	def widescreen(self):
		self._sendcommand(self.INQ_WIDEMODE)
		ret = self._getresponse()
		if (ret == None):
		   return None
		if (len(ret) > 0):
			if (ret[0] == 0x50):
			   if (ret[1] == 0x02):
				   return True
			   else:
				   return False
		return False

	@widescreen.setter
	def widescreen(self, wide=True):
		if (wide):
			self._sendcommand(self.WIDEON)
		else:
			self._sendcommand(self.WIDEOFF)

	@property
	def shutter(self):
		self._sendcommand(self.INQ_SHUTTER)
		ret = self._getresponse()
		if (ret == None):
			return 0
		if (len(ret) > 0):
			if (ret[0] == 0x50):
				return self._combinenibbles(ret[3:5])
		return 0
		
	@shutter.setter
	def shutter(self, position):
		self._sendcommand([0x01, 0x04, 0x4A, 0x00, 0x00] + self._splitnibbles(position, 2) + [0xFF])

	def reset_shutter(self):
		self._sendcommand(self.SHUTTERRESET)

	def increase_shutter(self):
		self._sendcommand(self.SHUTTERUP)

	def decrease_shutter(self):
		self._sendcommand(self.SHUTTERDOWN)

	@property
	def iris(self):
		self._sendcommand(self.INQ_IRIS)
		ret = self._getresponse()
		if (ret == None):
			return 0
		if (len(ret) > 0):
			if (ret[0] == 0x50):
				return self._combinenibbles(ret[3:5])
		return 0
		
	@iris.setter
	def iris(self, position):
		self._sendcommand([0x01, 0x04, 0x4B, 0x00, 0x00] + self._splitnibbles(position, 2) + [0xFF])

	def reset_iris(self):
		self._sendcommand(self.IRISRESET)

	def increase_iris(self):
		self._sendcommand(self.IRISUP)

	def decrease_iris(self):
		self._sendcommand(self.IRISDOWN)

	@property
	def gain(self):
		self._sendcommand(self.INQ_GAIN)
		ret = self._getresponse()
		if (ret == None):
			return 0
		if (len(ret) > 0):
			if (ret[0] == 0x50):
				return self._combinenibbles(ret[3:5])
		return 0
	
	@gain.setter
	def gain(self, amount):
		self._sendcommand([0x01, 0x04, 0x4B, 0x00, 0x00] + self._splitnibbles(amount, 2) + [0xFF])

	def reset_gain(self):
		self._sendcommand(self.GAINRESET)

	def increase_gain(self):
		self._sendcommand(self.GAINUP)

	def decrease_gain(self):
		self._sendcommand(self.GAINDOWN)

	@property
	def brightness(self):
		self._sendcommand(self.INQ_BRIGHTNESS)
		ret = self._getresponse()
		if (ret == None):
			return 0
		if (len(ret) > 0):
			if (ret[0] == 0x50):
				return self._combinenibbles(ret[3:5])
		return 0
	
	@brightness.setter
	def brightness(self, amount):
		self._sendcommand([0x01, 0x04, 0x4D, 0x00, 0x00] + self._splitnibbles(amount, 2) + [0xFF])

	def reset_brightness(self):
		self._sendcommand(self.BRIGHTNESSRESET)

	def increase_brightness(self):
		self._sendcommand(self.BRIGHTNESSUP)

	def decrease_brightness(self):
		self._sendcommand(self.BRIGHTNESSDOWN)

	@property
	def exp(self):
		self._sendcommand(self.INQ_EXP)
		ret = self._getresponse()
		if (ret == None):
			return 0
		if (len(ret) > 0):
			if (ret[0] == 0x50):
				return self._combinenibbles(ret[3:5])
		return 0
	
	@exp.setter
	def exp(self, amount):
		self._sendcommand([0x01, 0x04, 0x4E, 0x00, 0x00] + self._splitnibbles(amount, 2) + [0xFF])

	def reset_exp(self):
		self._sendcommand(self.EXPRESET)

	def increase_exp(self):
		self._sendcommand(self.EXPUP)

	def decrease_exp(self):
		self._sendcommand(self.EXPDOWN)

	@property
	def aperture(self):
		self._sendcommand(self.INQ_APERTURE)
		ret = self._getresponse()
		if (ret == None):
			return 0
		if (len(ret) > 0):
			if (ret[0] == 0x50):
				return self._combinenibbles(ret[3:5])
		return 0
	
	@aperture.setter
	def aperture(self, amount):
		self._sendcommand([0x01, 0x04, 0x42, 0x00, 0x00] + self._splitnibbles(amount, 2) + [0xFF])

	def reset_aperture(self):
		self._sendcommand(self.APERTURERESET)

	def increase_aperture(self):
		self._sendcommand(self.APERTUREUP)

	def decrease_aperture(self):
		self._sendcommand(self.APERTUREDOWN)

	@property
	def backlight(self):
		self._sendcommand(self.INQ_BACKLIGHT)
		ret = self._getresponse()
		if (ret != None):
			if (len(ret) > 0):
				if (ret == [0x50, 0x02]):
					return True
		return False

	@backlight.setter
	def backlight(self, value):
		if (value):
			self._sendcommand(self.BACKLIGHTON)
		else:
			self._sendcommand(self.BACKLIGHTOFF)

#end class VISCA

if (__name__ == "__main__"):
	print("Hello. Please import this module into your own program")
else:
	print("Thank you for using this module!")
