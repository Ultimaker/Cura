#Name: Tweak At Z 4.0.1
#Info: Change printing parameters at a given height
#Help: TweakAtZ
#Depend: GCode
#Type: postprocess
#Param: targetZ(float:5.0) Z height to tweak at (mm)
#Param: targetL(int:) (ALT) Layer no. to tweak at
#Param: twLayers(int:1) No. of layers used for change
#Param: behavior(list:Tweak value and keep it for the rest,Tweak value for single layer only) Tweak behavior
#Param: speed(int:) New TOTAL Speed (%)
#Param: printspeed(int:) New PRINT Speed (%)
#Param: flowrate(int:) New General Flow Rate (%)
#Param: flowrateOne(int:) New Flow Rate Extruder 1 (%)
#Param: flowrateTwo(int:) New Flow Rate Extruder 2 (%)
#Param: platformTemp(int:) New Bed Temp (deg C)
#Param: extruderOne(int:) New Extruder 1 Temp (deg C)
#Param: extruderTwo(int:) New Extruder 2 Temp (deg C)
#Param: fanSpeed(int:) New Fan Speed (0-255 PWM)

## Written by Steven Morlock, smorloc@gmail.com
## Modified by Ricardo Gomez, ricardoga@otulook.com, to add Bed Temperature and make it work with Cura_13.06.04+
## Modified by Stefan Heule, Dim3nsioneer@gmx.ch since V3.0 (see changelog below)
## This script is licensed under the Creative Commons - Attribution - Share Alike (CC BY-SA) terms

## Uses -
## M220 S<factor in percent> - set speed factor override percentage
## M221 S<factor in percent> - set flow factor override percentage
## M221 S<factor in percent> T<0-#toolheads> - set flow factor override percentage for single extruder
## M104 S<temp> T<0-#toolheads> - set extruder <T> to target temperature <S>
## M140 S<temp> - set bed target temperature
## M106 S<PWM> - set fan speed to target speed <S>
## M605/606 to save and recall material settings on the UM2

##history / changelog:
##V3.0.1: TweakAtZ-state default 1 (i.e. the plugin works without any TweakAtZ comment)
##V3.1:   Recognizes UltiGCode and deactivates value reset, fan speed added, alternatively layer no. to tweak at,
##        extruder three temperature disabled by '#Ex3'
##V3.1.1: Bugfix reset flow rate
##V3.1.2: Bugfix disable TweakAtZ on Cool Head Lift
##V3.2:   Flow rate for specific extruder added (only for 2 extruders), bugfix parser,
##        added speed reset at the end of the print
##V4.0:   Progress bar, tweaking over multiple layers, M605&M606 implemented, reset after one layer option,
##        extruder three code removed, tweaking print speed, save call of Publisher class,
##        uses previous value from other plugins also on UltiGCode
##V4.0.1: Bugfix for doubled G1 commands

version = '4.0.1'

import re
import wx
import time
try:
	#MacOS release currently lacks some wx components, like the Publisher.
	from wx.lib.pubsub import Publisher
except:
	Publisher = None

def getValue(line, key, default = None):
	if not key in line or (';' in line and line.find(key) > line.find(';') and
							   not ";TweakAtZ" in key and not ";LAYER:" in key):
		return default
	subPart = line[line.find(key) + len(key):] #allows for string lengths larger than 1
	if ";TweakAtZ" in key:
		m = re.search('^[0-4]', subPart)
	elif ";LAYER:" in key:
		m = re.search('^[+-]?[0-9]*', subPart)
	else:
		#the minus at the beginning allows for negative values, e.g. for delta printers
		m = re.search('^[-]?[0-9]+\.?[0-9]*', subPart)
	if m == None:
		return default
	try:
		return float(m.group(0))
	except:
		return default

with open(filename, "r") as f:
	lines = f.readlines()
#Check which tweaks should apply
TweakProp = {'speed': speed is not None and speed != '',
			 'flowrate': flowrate is not None and flowrate != '',
			 'flowrateOne': flowrateOne is not None and flowrateOne != '',
			 'flowrateTwo': flowrateTwo is not None and flowrateTwo != '',
			 'platformTemp': platformTemp is not None and platformTemp != '',
			 'extruderOne': extruderOne is not None and extruderOne != '',
			 'extruderTwo': extruderTwo is not None and extruderTwo != '',
			 'fanSpeed': fanSpeed is not None and fanSpeed != ''}
TweakPrintSpeed = printspeed is not None and printspeed != ''
TweakStrings = {'speed': "M220 S%f\n",
				'flowrate': "M221 S%f\n",
				'flowrateOne': "M221 T0 S%f\n",
				'flowrateTwo': "M221 T1 S%f\n",
				'platformTemp': "M140 S%f\n",
				'extruderOne': "M104 S%f T0\n",
				'extruderTwo': "M104 S%f T1\n",
				'fanSpeed': "M106 S%d\n"}
target_values = {}
for key in TweakProp:
	target_values[key]=eval(key)
old = {'speed': -1, 'flowrate': -1, 'flowrateOne': -1, 'flowrateTwo': -1, 'platformTemp': -1, 'extruderOne': -1,
	   'extruderTwo': -1, 'fanSpeed': -1, 'state': -1}
try:
	twLayers = max(int(twLayers),1) #for the case someone entered something as 'funny' as -1
except:
	twLayers = 1
pres_ext = 0
done_layers = 0
z = 0
x = None
y = None
layer = -100000 #layer no. may be negative (raft) but never that low
# state 0: deactivated, state 1: activated, state 2: active, but below z,
# state 3: active and partially executed (multi layer), state 4: active and passed z
state = 1
# IsUM2: Used for reset of values (ok for Marlin/Sprinter),
# has to be set to 1 for UltiGCode (work-around for missing default values)
IsUM2 = False
lastpercentage = 0
i = 0
l = len(lines)
oldValueUnknown = False
TWinstances = 0


try:
	targetL_i = int(targetL)
	targetZ = 100000
except:
	targetL_i = -100000

if Publisher is not None:
	if targetL_i > -100000:
		wx.CallAfter(Publisher().sendMessage, "pluginupdate",
					 "OpenPluginProgressWindow;TweakAtZ;Tweak At Z plugin is executed at layer " + str(targetL_i))
	else:
		wx.CallAfter(Publisher().sendMessage, "pluginupdate",
					 "OpenPluginProgressWindow;TweakAtZ;Tweak At Z plugin is executed at height " + str(targetZ) + "mm")
with open(filename, "w") as file:
	for line in lines:
		if int(i*100/l) > lastpercentage and Publisher is not None: #progressbar
			lastpercentage = int(i*100/l)
			wx.CallAfter(Publisher().sendMessage, "pluginupdate", "Progress;" + str(lastpercentage))
		if ';Layer count:' in line:
			TWinstances += 1
			file.write(';TweakAtZ instances: %d\n' % TWinstances)
		if not ('M84' in line or 'M25' in line or ('G1' in line and TweakPrintSpeed and state==3) or
						';TweakAtZ instances:' in line):
			file.write(line)
		IsUM2 = ('FLAVOR:UltiGCode' in line) or IsUM2 #Flavor is UltiGCode!
		if ';TweakAtZ-state' in line: #checks for state change comment
			state = getValue(line, ';TweakAtZ-state', state)
		if ';TweakAtZ instances:' in line:
			try:
				tempTWi = int(line[20:])
			except:
				tempTWi = TWinstances
			TWinstances = tempTWi
		if ';Small layer' in line: #checks for begin of Cool Head Lift
			old['state'] = state
			state = 0
		#if ('G4' in line) and old['state'] > -1:
		#old['state'] = -1
		if ';LAYER:' in line: #new layer no. found
			layer = getValue(line, ';LAYER:', layer)
			if targetL_i > -100000: #target selected by layer no.
				if state == 2 and layer >= targetL_i: #determine targetZ from layer no.
					targetZ = z + 0.001
		if (getValue(line, 'T', None) is not None) and (getValue(line, 'M', None) is None): #looking for single T-cmd
			pres_ext = getValue(line, 'T', pres_ext)
		if 'M190' in line or 'M140' in line and state < 3: #looking for bed temp, stops after target z is passed
			old['platformTemp'] = getValue(line, 'S', old['platformTemp'])
		if 'M109' in line or 'M104' in line and state < 3: #looking for extruder temp, stops after target z is passed
			if getValue(line, 'T', pres_ext) == 0:
				old['extruderOne'] = getValue(line, 'S', old['extruderOne'])
			elif getValue(line, 'T', pres_ext) == 1:
				old['extruderTwo'] = getValue(line, 'S', old['extruderTwo'])
		if 'M107' in line: #fan is stopped; is always updated in order not to miss switch off for next object
			old['fanSpeed'] = 0
		if 'M106' in line and state < 3: #looking for fan speed
			old['fanSpeed'] = getValue(line, 'S', old['fanSpeed'])
		if 'M221' in line and state < 3: #looking for flow rate
			tmp_extruder = getValue(line,'T',None)
			if tmp_extruder == None: #check if extruder is specified
				old['flowrate'] = getValue(line, 'S', old['flowrate'])
			elif tmp_extruder == 0: #first extruder
				old['flowrateOne'] = getValue(line, 'S', old['flowrateOne'])
			elif tmp_extruder == 1: #second extruder
				old['flowrateOne'] = getValue(line, 'S', old['flowrateOne'])
		if ('M84' in line or 'M25' in line):
			if state>0 and speed is not None and speed != '': #'finish' commands for UM Original and UM2
				file.write("M220 S100 ; speed reset to 100% at the end of print\n")
				file.write("M117                     \n")
			file.write(line)
		if 'G1' in line or 'G0' in line:
			newZ = getValue(line, 'Z', z)
			x = getValue(line, 'X', None)
			y = getValue(line, 'Y', None)
			e = getValue(line, 'E', None)
			f = getValue(line, 'F', None)
			if TweakPrintSpeed and state==3:
				# check for pure print movement in target range:
				if 'G1' in line and x != None and y != None and f != None and e != None and newZ==z:
					file.write("G1 F%d X%1.3f Y%1.3f E%1.5f\n" % (int(f/100.0*float(printspeed)),getValue(line,'X'),
																  getValue(line,'Y'),getValue(line,'E')))
                                else: #G1 command but not a print movement
                                        file.write(line)
			# no tweaking on retraction hops which have no x and y coordinate:
			if (newZ != z) and (x is not None) and (y is not None):
				z = newZ
				if z < targetZ and state == 1:
					state = 2
				if z >= targetZ and state == 2:
					state = 3
					done_layers = 0
					for key in TweakProp:
						if TweakProp[key] and old[key]==-1: #old value is not known
							oldValueUnknown = True
					if oldValueUnknown: #the tweaking has to happen within one layer
						twLayers = 1
						if IsUM2: #Parameters have to be stored in the printer (UltiGCode=UM2)
							file.write("M605 S%d;stores parameters before tweaking\n" % (TWinstances-1))
					if behavior == 1: #single layer tweak only and then reset
						twLayers = 1
					if TweakPrintSpeed and behavior == 0:
						twLayers = done_layers + 1
				if state==3:
					if twLayers-done_layers>0: #still layers to go?
						if targetL_i > -100000:
							file.write(";TweakAtZ V%s: executed at Layer %d\n" % (version,layer))
							file.write("M117 Printing... tw@L%4d\n" % layer)
						else:
							file.write(";TweakAtZ V%s: executed at %1.2f mm\n" % (version,z))
							file.write("M117 Printing... tw@%5.1f\n" % z)
						for key in TweakProp:
							if TweakProp[key]:
								file.write(TweakStrings[key] %
										   float(old[key]+(float(target_values[key])-
														   float(old[key]))/float(twLayers)*float(done_layers+1)))
						done_layers += 1
					else:
						state = 4
						if behavior == 1: #reset values after one layer
							if targetL_i > -100000:
								file.write(";TweakAtZ V%s: reset on Layer %d\n" % (version,layer))
							else:
								file.write(";TweakAtZ V%s: reset at %1.2f mm\n" % (version,z))
							if not oldValueUnknown:
								if not IsUM2:#executes only for UM Original and UM2 with RepRap flavor
									for key in TweakProp:
										if TweakProp[key]:
											file.write(TweakStrings[key] % float(old[key]))
								else: #executes on UM2 with Ultigcode
									file.write("M606 S%d;recalls saved settings\n" % (TWinstances-1))
				# re-activates the plugin if executed by pre-print G-command, resets settings:
				if z < targetZ and state >= 3:
					state = 2
					done_layers = 0
					if targetL_i > -100000:
						file.write(";TweakAtZ V%s: reset below Layer %d\n" % (version,targetL_i))
					else:
						file.write(";TweakAtZ V%s: reset below %1.2f mm\n" % (version,targetZ))
					if not IsUM2: #executes only for UM Original and UM2 with RepRap flavor
						for key in TweakProp:
							if TweakProp[key]:
								file.write(TweakStrings[key] % float(old[key]))
					else:
						file.write("M606 ;recalls saved settings\n")
		i+=1
if Publisher is not None:
	wx.CallAfter(Publisher().sendMessage, "pluginupdate", "Progress;100")
	time.sleep(1)
	wx.CallAfter(Publisher().sendMessage, "pluginupdate", "ClosePluginProgressWindow")
