#Name: Tweak At Z 3.2
#Info: Change printing parameters at a given height
#Help: TweakAtZ
#Depend: GCode
#Type: postprocess
#Param: targetZ(float:5.0) Z height to tweak at (mm)
#Param: targetL(int:) (ALT) Layer no. to tweak at
#Param: speed(int:) New Speed (%)
#Param: flowrate(int:) New General Flow Rate (%)
#Param: flowrateOne(int:) New Flow Rate Extruder 1 (%)
#Param: flowrateTwo(int:) New Flow Rate Extruder 2 (%)
#Param: platformTemp(int:) New Bed Temp (deg C)
#Param: extruderOne(int:) New Extruder 1 Temp (deg C)
#Param: extruderTwo(int:) New Extruder 2 Temp (deg C)
#Ex3 #Param: extruderThree(int:) New Extruder 3 Temp (deg C)
#Param: fanSpeed(int:) New Fan Speed (0-255 PWM)

## Written by Steven Morlock, smorloc@gmail.com
## Modified by Ricardo Gomez, ricardoga@otulook.com, to add Bed Temperature and make it work with Cura_13.06.04+
## Modified by Stefan Heule, Dim3nsioneer@gmx.ch, to add Flow Rate, restoration of initial values when returning to low Z, extended stage numbers, direct stage manipulation by GCODE-comments, UltiGCode regocnition, addition of fan speed, alternative selection by layer no., disabling extruder three, addition of flow rate for specific extruder
## This script is licensed under the Creative Commons - Attribution - Share Alike (CC BY-SA) terms

# Uses -
# M220 S<factor in percent> - set speed factor override percentage
# M221 S<factor in percent> - set flow factor override percentage
# M221 S<factor in percent> T<0-#toolheads> - set flow factor override percentage for single extruder
# M104 S<temp> T<0-#toolheads> - set extruder <T> to target temperature <S>
# M140 S<temp> - set bed target temperature
# M106 S<PWM> - set fan speed to target speed <S>

#history / changelog:
#V3.0.1: TweakAtZ-state default 1 (i.e. the plugin works without any TweakAtZ comment)
#V3.1:   Recognizes UltiGCode and deactivates value reset, fan speed added, alternatively layer no. to tweak at, extruder three temperature disabled by '#Ex3'
#V3.1.1: Bugfix reset flow rate
#V3.1.2: Bugfix disable TweakAtZ on Cool Head Lift
#V3.2:   Flow rate for specific extruder added (only for 2 extruders), bugfix parser, added speed reset at the end of the print

version = '3.2'

import re

def getValue(line, key, default = None):
	if not key in line or (';' in line and line.find(key) > line.find(';') and not ";TweakAtZ" in key and not ";LAYER:" in key):
		return default
	subPart = line[line.find(key) + len(key):] #allows for string lengths larger than 1
        if ";TweakAtZ" in key:
                m = re.search('^[0-3]', subPart)
        elif ";LAYER:" in key:
                m = re.search('^[+-]?[0-9]*', subPart)
        else:
                m = re.search('^[-]?[0-9]+\.?[0-9]*', subPart) #the minus at the beginning allows for negative values, e.g. for delta printers
	if m == None:
		return default
	try:
		return float(m.group(0))
	except:
		return default

with open(filename, "r") as f:
	lines = f.readlines()

old_speed = 100
old_flowrate = 100
old_flowrateOne = 100
old_flowrateTwo = 100
old_platformTemp = -1
old_extruderOne = -1
old_extruderTwo = -1
#Ex3 old_extruderThree = -1
old_fanSpeed = 0
pres_ext = 0
z = 0
x = None
y = None
layer = -100000 #layer no. may be negative (raft) but never that low
state = 1 #state 0: deactivated, state 1: activated, state 2: active, but below z, state 3: active, passed z
old_state = -1
no_reset = 0 #Default setting is reset (ok for Marlin/Sprinter), has to be set to 1 for UltiGCode (work-around for missing default values)

try:
        targetL_i = int(targetL)
        targetZ = 100000
except:
        targetL_i = -100000

with open(filename, "w") as f:
	for line in lines:
		if not ('M84' in line or 'M25' in line):
                        f.write(line)
                if 'FLAVOR:UltiGCode' in line: #Flavor is UltiGCode! No reset of values
                        no_reset = 1
                if ';TweakAtZ-state' in line: #checks for state change comment
                        state = getValue(line, ';TweakAtZ-state', state)
                if ';Small layer' in line: #checks for begin of Cool Head Lift
                        old_state = state
                        state = 0
                if ('G4' in line) and old_state > -1:
                        state = old_state
                        old_state = -1
                if ';LAYER:' in line: #new layer no. found
                        layer = getValue(line, ';LAYER:', layer)
                        if targetL_i > -100000: #target selected by layer no.
                                if state == 2 and layer >= targetL_i: #determine targetZ from layer no.
                                        targetZ = z + 0.001
                if (getValue(line, 'T', None) is not None) and (getValue(line, 'M', None) is None): #looking for single T-command
                        pres_ext = getValue(line, 'T', pres_ext)
                if 'M190' in line or 'M140' in line and state < 3: #looking for bed temp, stops after target z is passed
                        old_platformTemp = getValue(line, 'S', old_platformTemp)
                if 'M109' in line or 'M104' in line and state < 3: #looking for extruder temp, stops after target z is passed
                        if getValue(line, 'T', pres_ext) == 0:
                                old_extruderOne = getValue(line, 'S', old_extruderOne)
                        elif getValue(line, 'T', pres_ext) == 1:
                                old_extruderTwo = getValue(line, 'S', old_extruderTwo)
#Ex3                        elif getValue(line, 'T', pres_ext) == 2:
#Ex3                                old_extruderThree = getValue(line, 'S', old_extruderThree)
                if 'M107' in line: #fan is stopped; is always updated in order not to miss switch off for next object
                        old_fanSpeed = 0
                if 'M106' in line and state < 3: #looking for fan speed
                        old_fanSpeed = getValue(line, 'S', old_fanSpeed)
                if 'M221' in line and state < 3: #looking for flow rate
                        tmp_extruder = getValue(line,'T',None)
                        if tmp_extruder == None: #check if extruder is specified
                                old_flowrate = getValue(line, 'S', old_flowrate)
                        else:
                                if tmp_extruder == 0: #first extruder
                                        old_flowrateOne = getValue(line, 'S', old_flowrateOne)
                                if tmp_extruder == 1: #second extruder
                                        old_flowrateOne = getValue(line, 'S', old_flowrateOne)
                if ('M84' in line or 'M25' in line):
                        if state>0 and speed is not None and speed != '': #'finish' commands for UM Original and UM2
                                f.write("M220 S100 ; speed reset to 100% at the end of print\n");
                                f.write("M117                     \n")
                        f.write(line)
		if 'G1' in line or 'G0' in line:
			newZ = getValue(line, 'Z', z)
			x = getValue(line, 'X', None)
			y = getValue(line, 'Y', None)
			if (newZ != z) and (x is not None) and (y is not None): #no tweaking on retraction hops which have no x and y coordinate
				z = newZ
				if z < targetZ and state == 1:
					state = 2
				if z >= targetZ and state == 2:
					state = 3
                                        if targetL_i > -100000:
                                                f.write(";TweakAtZ V%s: executed at Layer %d\n" % (version,targetL_i))
                                                f.write("M117 Printing... tw@L%4d\n" % targetL_i)
                                        else:
                                                f.write(";TweakAtZ V%s: executed at %1.2f mm\n" % (version,targetZ))
                                                f.write("M117 Printing... tw@%5.1f\n" % targetZ)
					if speed is not None and speed != '':
						f.write("M220 S%f\n" % float(speed))
					if flowrate is not None and flowrate != '':
						f.write("M221 S%f\n" % float(flowrate))
					if flowrateOne is not None and flowrateOne != '':
						f.write("M221 T0 S%f\n" % float(flowrateOne))
					if flowrateTwo is not None and flowrateTwo != '':
						f.write("M221 T1 S%f\n" % float(flowrateTwo))
					if platformTemp is not None and platformTemp != '':
						f.write("M140 S%f\n" % float(platformTemp))
					if extruderOne is not None and extruderOne != '':
						f.write("M104 S%f T0\n" % float(extruderOne))
					if extruderTwo is not None and extruderTwo != '':
						f.write("M104 S%f T1\n" % float(extruderTwo))
#Ex3					if extruderThree is not None and extruderThree != '':
#Ex3						f.write("M104 S%f T2\n" % float(extruderThree))					
					if fanSpeed is not None and fanSpeed != '':
						f.write("M106 S%d\n" % int(fanSpeed))					
                                if z < targetZ and state == 3: #re-activates the plugin if executed by pre-print G-command, resets settings
                                        state = 2
                                        if no_reset == 0: #executes only for UM Original and UM2 with RepRap flavor
                                                if targetL_i > -100000:
                                                        f.write(";TweakAtZ V%s: reset below Layer %d\n" % (version,targetL_i))
                                                else:
                                                        f.write(";TweakAtZ V%s: reset below %1.2f mm\n" % (version,targetZ))
                                                if speed is not None and speed != '':
                                                        f.write("M220 S%f\n" % float(old_speed))
                                                if flowrate is not None and flowrate != '':
                                                        f.write("M221 S%f\n" % float(old_flowrate))
                                                if flowrateOne is not None and flowrateOne != '':
                                                        f.write("M221 T0 S%f\n" % float(old_flowrateOne))
                                                if flowrateTwo is not None and flowrateTwo != '':
                                                        f.write("M221 T1 S%f\n" % float(old_flowrateTwo))
                                                if platformTemp is not None and platformTemp != '':
                                                        f.write("M140 S%f\n" % float(old_platformTemp))
                                                if extruderOne is not None and extruderOne != '':
                                                        f.write("M104 S%f T0\n" % float(old_extruderOne))
                                                if extruderTwo is not None and extruderTwo != '':
                                                        f.write("M104 S%f T1\n" % float(old_extruderTwo))
#Ex3                                                if extruderThree is not None and extruderThree != '':
#Ex3                                                        f.write("M104 S%f T2\n" % float(old_extruderThree))					
                                                if fanSpeed is not None and fanSpeed != '':
                                                        f.write("M106 S%d;\n" % int(old_fanSpeed))					
				
