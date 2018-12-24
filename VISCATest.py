#! /usr/local/bin/python3
from pyvisca import visca
from time import sleep, time
import pygame

def wait(s):
	for i in range(s, 0, -1):
		print(i)
		sleep(1)

def processSerialInput(serial):
	if (serial.in_waiting > 0):
		readbytes = serial.read(serial.in_waiting)
		inputs = readbytes.split(bytes([0xFF]))
		for input in inputs:
			if (len(input) > 0):
				s = ""
				address = (list(input)[:1][0] - 0x80) >> 4
				response = list(input)[1:]
				if (response == [0x60, 0x02]):
					s = "Syntax error"
				elif (response == [0x61, 0x41]):
					s = "Command not executable"
				elif (response == [0x41]):
					#s = "Command accepted"
					pass
				elif (response == [0x51]):
					#s = "Command completed"
					pass
				else:
					s = str([hex(c) for c in response])
				if (s != ""):
					print("RESPONSE (camera " + str(address) + "): " + s)

SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480

quitNow = False
cameraMoving = False
cameraZooming = False
cameraFocusing = False
lastSettingsCheck = 0
menuOn = False
wideModeOn = False
backlightOn = False

print("Initializing stuff")
cam = visca.Camera('/dev/tty.usbserial', 38400)

cam.debug_mode=False

print(cam.getVersionInfo())

pygame.init()
pygame.display.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
surface = pygame.Surface(screen.get_size()).convert()

print("Drawing to screen")
surface.fill((64, 64, 64))      
screen.blit(surface, (0, 0))
pygame.display.flip()
pygame.display.update()
			
print("\nCONTROLS\n")
print("ARROW KEYS:\t\tpan and tilt - use SHIFT to move quickly")
print("P:\t\t\tdisplay current pan and tilt position")
print("0:\t\t\treturn to home position")
print("F:\t\t\tfreeze image, SHIFT to unfreeze")
print("R:\t\t\tred gain, SHIFT to increase, CTRL to decrease, ALT to reset")
print("B:\t\t\tblue gain, SHIFT to increase, CTRL to decrease, ALT to reset")
print("I:\t\t\tiris gain, SHIFT to increase, CTRL to decrease, ALT to reset")
print("G:\t\t\tgain, SHIFT to increase, CTRL to decrease, ALT to reset")
print("L:\t\t\tbrightness, SHIFT to increase, CTRL to decrease, ALT to reset")
print("X:\t\t\texposure compensation, SHIFT to increase, CTRL to decrease, ALT to reset")
print("S:\t\t\tshutter, SHIFT to increase, CTRL to decrease, ALT to reset")
print("A:\t\t\taperture, SHIFT to increase, CTRL to decrease, ALT to reset")
print("K:\t\t\tbacklight toggle")
print("1 - 5 (above letters):\trecall preset, use CTRL to save and ALT to delete")
print("1 - 5 (num pad):\tset auto exposure mode to auto, manual, shutter priority, iris priority, bright manual")
print("F1:\t\t\tmenu")
print("F2:\t\t\ttoggle wide mode")
print("ENTER:\t\t\tmenu OK")
print("BACKSPACE\t\tmenu back")
print("F9:\t\t\tpower, use CTRL to turn on, ALT to turn off")
print("F10:\t\t\ttally light, use CTRL to turn on, ALT to turn off")
print("F12:\t\t\treset camera")
print("+/-:\t\t\tzoom in and out, use SHIFT to move quickly")
print("[/]:\t\t\tfocus near and far")
print("F4 - F8:\t\tset white balance to manual, auto, indoor, outdoor, or one-push manual")
print("ESCAPE or Q:\t\tquit")
print("\n\n")

print("Starting main loop")
while (not quitNow):
	sleep(0.1)

	# get serial input
	processSerialInput(cam._serial)
	
	# get input
	keys = pygame.key.get_pressed()
	mods = pygame.key.get_mods()

	# Check for quit event
	if (len(pygame.event.get(pygame.QUIT)) > 0):
		quitNow = True

	# Check for escape press
	if (keys[pygame.K_ESCAPE] or keys[pygame.K_q]):
		quitNow = True

	if (not quitNow):
		if (mods & pygame.KMOD_SHIFT):
			moveSpeed = 0x18
			zoomSpeed = 0x07
		else:
			moveSpeed = 0x07
			zoomSpeed = 0x03

		# Handle movement keys (handled separately because we need to know when they're released, and they have unique combinations)
		arrowKeys = [keys[pygame.K_UP], keys[pygame.K_DOWN], keys[pygame.K_RIGHT], keys[pygame.K_LEFT]]
		if (arrowKeys == [True, False, False, False]):
			#Up only
			cam.move_up(moveSpeed)
			cameraMoving = True
		elif (arrowKeys == [False, True, False, False]):
			#Down only
			cam.move_down(moveSpeed)
			cameraMoving = True
		elif (arrowKeys == [False, False, True, False]):
			#Right only
			cam.move_right(moveSpeed)
			cameraMoving = True
		elif (arrowKeys == [False, False, False, True]):
			#Left only
			cam.move_left(moveSpeed)
			cameraMoving = True
		elif (arrowKeys == [True, False, True, False]):
			#Up-right
			cam.move_upright(moveSpeed)
			cameraMoving = True
		elif (arrowKeys == [True, False, False, True]):
			#Up-left
			cam.move_upleft(moveSpeed)
			cameraMoving = True
		elif (arrowKeys == [False, True, True, False]):
			#Down-right
			cam.move_downright(moveSpeed)
			cameraMoving = True
		elif (arrowKeys == [False, True, False, True]):
			#Down-left
			cam.move_downleft(moveSpeed)
			cameraMoving = True
		else:
			#No movement or invalid combination
			if (cameraMoving):
				cam.move_stop()
				cameraMoving = False

		# Handle zooming (handled separately because we need to know when they're released)
		if (keys[pygame.K_EQUALS] or keys[pygame.K_KP_PLUS]):
			# zoom in
			if (not cameraZooming):
				cam.zoom_in(zoomSpeed)
				cameraZooming = True
		elif (keys[pygame.K_MINUS] or keys[pygame.K_KP_MINUS]):
			# zoom out
			if (not cameraZooming):
				cam.zoom_out(zoomSpeed)
				cameraZooming = True         
		else:
			if (cameraZooming):
				cam.zoom_stop()
				cameraZooming = False

		# Handle focusing (handled separately because we need to know when they're released)
		if (keys[pygame.K_RIGHTBRACKET]):
			# focus far
			if (not cameraFocusing):
				cam.autofocus = False
				cam.focus_far()
				cameraFocusing = True
		elif (keys[pygame.K_LEFTBRACKET]):
			# focus near
			if (not cameraFocusing):
				cam.autofocus = False
				cam.focus_near()
				cameraFocusing = True
		else:
			if (cameraFocusing):
				cam.focus_stop()
				cameraFocusing = False
				
		# This giant if statement handles all other key presses
		if (keys[pygame.K_BACKSLASH]):
			cam.autofocus = True
		elif (keys[pygame.K_p]):
			# Print current pan and tilt position
			print(cam.get_pantilt())

		# Handle presets
		elif (keys[pygame.K_1]):
			if (mods & pygame.KMOD_SHIFT):
				cam.store_preset(0)
			elif (mods & pygame.KMOD_ALT):
				cam.clear_preset(0)
			else:
				cam.preset = 0
		elif (keys[pygame.K_2]):
			if (mods & pygame.KMOD_SHIFT):
				cam.store_preset(1)
			elif (mods & pygame.KMOD_ALT):
				cam.clear_preset(1)
			else:
				cam.preset = 1
		elif (keys[pygame.K_3]):
			if (mods & pygame.KMOD_SHIFT):
				cam.store_preset(2)
			elif (mods & pygame.KMOD_ALT):
				cam.clear_preset(2)
			else:
				cam.preset = 2
		elif (keys[pygame.K_4]):
			if (mods & pygame.KMOD_SHIFT):
				cam.store_preset(3)
			elif (mods & pygame.KMOD_ALT):
				cam.clear_preset(3)
			else:
				cam.preset = 3
		elif (keys[pygame.K_5]):
			if (mods & pygame.KMOD_SHIFT):
				cam.store_preset(4)
			elif (mods & pygame.KMOD_ALT):
				cam.clear_preset(4)
			else:
				cam.preset = 4
		elif (keys[pygame.K_6]):
			if (mods & pygame.KMOD_SHIFT):
				cam.store_preset(5)
			elif (mods & pygame.KMOD_ALT):
				cam.clear_preset(5)
			else:
				cam.preset = 5

		# Handle misc other keys
		elif (keys[pygame.K_F12]):
			cam.reset()

		elif (keys[pygame.K_0]):
			cam.home()

		# Handle power keys
		elif (keys[pygame.K_F9]):
			if (mods & pygame.KMOD_CTRL):
				cam.power_on = True
			elif (mods & pygame.KMOD_ALT):
				cam.power_on = False
			else:
				pwr = cam.power_on
				if (pwr == None):
					print("Error getting camera power status")
				elif (pwr):
					print("Camera is ON")
				else:
					print("Camera is off")

		# Handle tally keys
		elif (keys[pygame.K_F10]):
			if (mods & pygame.KMOD_CTRL):
				cam.tally_on = True
			elif (mods & pygame.KMOD_ALT):
				cam.tally_on = False
			else:
				tly = cam.tally_on
				if (tly == None):
					print("Error getting tally light status")
				elif (tly):
					print("Tally light is ON")
				else:
					print("Tally light is off")

		# Handle white balance keys
		elif (keys[pygame.K_F4]):
			cam.white_balance = cam.WhiteBalance.MANUAL
		elif (keys[pygame.K_F5]):
			cam.white_balance = cam.WhiteBalance.AUTO
		elif (keys[pygame.K_F6]):
			cam.white_balance = cam.WhiteBalance.INDOOR
		elif (keys[pygame.K_F7]):
			cam.white_balance = cam.WhiteBalance.OUTDOOR
		elif (keys[pygame.K_F8]):
			cam.white_balance = cam.WhiteBalance.ONEPUSH

		elif (keys[pygame.K_r]):
			if (mods & pygame.KMOD_SHIFT):
				#increase red
				cam.increase_red_gain()
			elif (mods & pygame.KMOD_CTRL):
				#decrease red
				cam.decrease_red_gain()
			elif (mods & pygame.KMOD_ALT):
				#reset red
				print("Resetting red gain")
				cam.reset_red_gain()
			else:
				#get red
				print("Red gain: " + hex(cam.red_gain))

		elif (keys[pygame.K_b]):
			if (mods & pygame.KMOD_SHIFT):
				#increase blue
				cam.increase_blue_gain()
			elif (mods & pygame.KMOD_CTRL):
				#decrease blue
				cam.decrease_blue_gain()
			elif (mods & pygame.KMOD_ALT):
				#reset blue
				print("Resetting blue gain")
				cam.reset_blue_gain()
			else:
				#get blue
				print("Blue gain: " + hex(cam.blue_gain))
				
		# Handle autoexposure keys
		elif (keys[pygame.K_KP1]):
			cam.ae_mode = cam.AutoExposure.AUTO
		elif (keys[pygame.K_KP2]):
			cam.ae_mode = cam.AutoExposure.MANUAL
		elif (keys[pygame.K_KP3]):
			cam.ae_mode = cam.AutoExposure.SHUTTER_PRIORITY
		elif (keys[pygame.K_KP4]):
			cam.ae_mode = cam.AutoExposure.IRIS_PRIORITY
		elif (keys[pygame.K_KP5]):
			cam.ae_mode = cam.AutoExposure.BRIGHT

		# Handle freeze/unfreeze
		elif (keys[pygame.K_f]):
			if (mods & pygame.KMOD_SHIFT):
				cam.freeze = False
			else:
				cam.freeze = True
		# Handle menu keys
		elif (keys[pygame.K_F1]):
			menuOn = not menuOn
			if (menuOn):
				print("Showing menu")
				cam.menu_show()
			else:
				print("Hiding menu")
				cam.menu_hide()
			sleep(0.5)

		# Handle menu keys
		elif (keys[pygame.K_RETURN]):
			cam.menu_ok()
		elif (keys[pygame.K_BACKSPACE]):
			cam.menu_back()

		# Handle wide mode keys
		elif (keys[pygame.K_F2]):
			wideModeOn = not wideModeOn
			if (wideModeOn):
				cam.widescreen = True
			else:
				cam.widescreen = False

		# Handle exposure keys
		elif (keys[pygame.K_s]):
			if (mods & pygame.KMOD_SHIFT):
				cam.increase_shutter()
			elif (mods & pygame.KMOD_CTRL):
				cam.decrease_shutter()
			elif (mods & pygame.KMOD_ALT):
				print("Resetting shutter")
				cam.reset_shutter()
			else:
				print("Shutter: " + hex(cam.shutter))
		elif (keys[pygame.K_i]):
			if (mods & pygame.KMOD_SHIFT):
				cam.increase_iris()
			elif (mods & pygame.KMOD_CTRL):
				cam.decrease_iris()
			elif (mods & pygame.KMOD_ALT):
				print("Resetting iris")
				cam.reset_iris()
			else:
				print("Iris: " + hex(cam.iris))
		elif (keys[pygame.K_g]):
			if (mods & pygame.KMOD_SHIFT):
				cam.increase_gain()
			elif (mods & pygame.KMOD_CTRL):
				cam.decrease_gain()
			elif (mods & pygame.KMOD_ALT):
				print("Resetting gain")
				cam.reset_gain()
			else:
				print("Gain: " + hex(cam.gain))
		elif (keys[pygame.K_l]):
			if (mods & pygame.KMOD_SHIFT):
				cam.increase_brightness()
			elif (mods & pygame.KMOD_CTRL):
				cam.decrease_brightness()
			elif (mods & pygame.KMOD_ALT):
				print("Resetting brightness")
				cam.reset_brightness()
			else:
				print("Brightness: " + hex(cam.brightness))
		elif (keys[pygame.K_x]):
			if (mods & pygame.KMOD_SHIFT):
				cam.increase_exp()
			elif (mods & pygame.KMOD_CTRL):
				cam.decrease_exp()
			elif (mods & pygame.KMOD_ALT):
				print("Resetting exposure compensation")
				cam.reset_exp()
			else:
				print("Exposure compensation: " + hex(cam.exp))
		elif (keys[pygame.K_a]):
			if (mods & pygame.KMOD_SHIFT):
				cam.increase_aperture()
			elif (mods & pygame.KMOD_CTRL):
				cam.decrease_aperture()
			elif (mods & pygame.KMOD_ALT):
				print("Resetting aperture")
				cam.reset_aperture()
			else:
				print("Aperture: " + hex(cam.aperture))
		elif (keys[pygame.K_k]):
			backlightOn = not backlightOn
			cam.backlight = backlightOn
			print(cam.backlight)
			
		# Get settings
		if (time() - lastSettingsCheck > 1):
			#print("White balance mode: " + str(cam.white_balance))
			#print("AE mode:" + str(cam.ae_mode))
			#print("Image flip: " + str(cam.image_flip))
			#print("Pan reverse: " + str(cam.pan_reverse))
			#print("Tilt reverse: " + str(cam.tilt_reverse))
			lastSettingsCheck = time()
#end main while loop

print("Quitting normally")
pygame.quit()
