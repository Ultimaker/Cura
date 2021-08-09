# Color switching Tower Genaration
# This script is specific for the ZONESTAR M3 and M4 3d printer 
# It runs with the PostProcessingPlugin which is released under the terms of the AGPLv3 or higher.
# This script is licensed under the Creative Commons - Attribution - Share Alike (CC BY-SA) terms

# Authors of the Color switching Tower Genaration plug-in / script:
# Written by Hally.Zhong - hally@zonestar3d.com

#history / change-log:
#V1.0.5 - add line to extruder filament at every time when printing the tower
#
#V1.0.4 - use absolute Z heigth for Z hop
#
#V1.0.3 - Use auto retract to retract all extruder for mixing color printer
#
#V1.0.2 - add retract in the previous extruder when go to the tower
#
#V1.0.1 - Initial

import re
from ..Script import Script

class ColorSwitchTower_V1_0_7(Script):
    def __init__(self):
        super().__init__()
        
    def getSettingDataString(self):
        return """{
            "name": "ZONESTAR Color Switch Tower Genaration V1.0.7",
            "key": "ColorSwitchTowerV107",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "pattern_type":
                {
                    "label": "Pattern",
                    "description": "Pattern Type is line or square",
                    "type": "enum",
                    "options": {
                        "line":"Line",
                        "square":"Square"
                    },
                    "default_value": "line"
                },
                "line_width":
                {
                    "label": "Line width",
                    "description": "= line width of tower, recommended value is between 1 and 1.3 times of the nozzle size",
                    "type": "float",
                    "unit": "mm",
                    "default_value": 0.4,
                    "minimum_value": 0.2,
                    "maximum_value": 0.8
                },
                "used_color":
                {
                    "label": "Used color",
                    "description": "The maxium colors used at the same layer in the import gcode file, between 3 ~ 8",
                    "type": "int",
                    "default_value": 3,
                    "maximum_value": 8
                },
                "maxium_layer":
                {
                    "label": "Maxium layer",
                    "description": "Apply the tower to the layers less than this value, '0' means apply to all of the layers",
                    "type": "int",
                    "default_value": 0,
                    "minimum_value": -1,
                    "maximum_value": 1000000
                },
                "tower_start_x":
                {
                    "label": "x of the tower",
                    "description": "Value to start position at X axis (mm), between 0 ~ 1000",
                    "type": "int",
                    "unit": "mm",
                    "default_value": 150,
                    "minimum_value": 0,
                    "maximum_value": 1000
                },
                "tower_start_y":
                {
                    "label": "y of the tower",
                    "description": "Value to start position at Y axis (mm), between 0 ~ 1000",
                    "type": "int",
                    "unit": "mm",
                    "default_value": 200,
                    "minimum_value": 0,
                    "maximum_value": 1000
                },
                "tower_length":
                {
                    "label": "Tower Length",
                    "description": "Value to the length (at X axis) of the tower (mm), between 20 ~ 100",
                    "type": "int",
                    "unit": "mm",
                    "default_value": 60,
                    "minimum_value": 20,
                    "maximum_value": 100
                },
                "flow_length":
                {
                    "label": "Flow length",
                    "description": "Need to be extruded filament length when switch to a new color (mm), between 10 ~ 100",
                    "type": "int",
                    "unit": "mm",
                    "default_value": 50,
                    "minimum_value": 10,
                    "maximum_value": 100
                },
                "print_speed":
                {
                    "label": "Print speed",
                    "description": "printing speed of the tower, recommended value between 30 ~ 60",
                    "type": "int",
                    "unit": "mm/s",
                    "default_value": 50,
                    "minimum_value": 10,
                    "maximum_value": 100
                },
                "speed_firstlayer":
                {
                    "label": "First layer speed",
                    "description": "printing speed of the tower on the first layer, percent of the print speed",
                    "type": "int",
                    "unit": "%",
                    "default_value": 60,
                    "minimum_value": 50,
                    "maximum_value": 100
                },
                "retract_type":
                {
                    "label": "Retract type",
                    "description": "Strength level of retraction, simple:only operate the current extruder. enhanced:operate the current and previous extruder, strong: operate all extruders",
                    "type": "enum",
                    "options": {
                        "simple":"simply retract",
                        "enhanced":"enhanced retract",
                        "strong":"strong retract"
                    },
                    "default_value": "simple"
                },
                "anti_scratch":
                {
                    "label": "Anti scraping filament",
                    "description": "Add extrusion in the tower to prevent scraping filament after some retraction",
                    "type": "bool",
                    "default_value": false
                },
                "retraction_length":
                {
                    "label": "Retraction length",
                    "description": "Value to retract length when go to or leave the tower(mm), between 5 ~ 20",
                    "type": "int",
                    "unit": "mm",
                    "default_value": 10,
                    "minimum_value": 5,
                    "maximum_value": 20   
                },
                "retraction_speed":
                {
                    "label": "Retraction speed",
                    "description": "Value to retract speed when go to or leave the tower(mm/s), between 15 ~ 40",
                    "type": "int",
                    "unit": "mm/s",
                    "default_value": 30,
                    "minimum_value": 15,
                    "maximum_value": 45
                },
                "recover_length":
                {
                    "label": "Recover length",
                    "description": "Value to recover length after retraction (mm), between 0 ~ 0.3",
                    "type": "float",
                    "unit": "mm",
                    "default_value": 0.0,
                    "maximum_value": 0.30
                },
                "recover_speed":
                {
                    "label": "Recover speed",
                    "description": "Value to recover speed (mm/s), between 15 ~ 40",
                    "type": "int",
                    "unit": "mm/s",
                    "default_value": 15,
                    "minimum_value": 10,
                    "maximum_value": 40
                },
                "z_hop":
                {
                    "label": "Z Hop",
                    "description": "Enable z axis hop",
                    "type": "bool",
                    "default_value": true
                },
                "zhop_heigth":
                {
                    "label": "Z Hop heigth",
                    "description": "Z axis hop heigth when go to and leave the tower(mm)",
                    "type": "float",
                    "unit": "mm",
                    "default_value": 0.5,
                    "minimum_value": 0.2,
                    "maximum_value": 2.0,
                    "enabled": "z_hop"
                },
                "remove_M104":
                {
                    "label": "Remove unexpected M104",
                    "description": "Remove redundant temperature setting instructions",
                    "type": "bool",
                    "default_value": true
                }
            }
        }"""
        
    def execute(self, data):
        colors = self.getSettingValueByKey("used_color")
        startx = self.getSettingValueByKey("tower_start_x")
        starty = self.getSettingValueByKey("tower_start_y")     
        linewidth = round(self.getSettingValueByKey("line_width"),2)
        towerlength = self.getSettingValueByKey("tower_length")
        flowlength = self.getSettingValueByKey("flow_length")
        printspeed =  self.getSettingValueByKey("print_speed") * 60
        speedfirstlayer =   int(printspeed * self.getSettingValueByKey("speed_firstlayer") / 100)
        retractionlength = self.getSettingValueByKey("retraction_length")
        retractionspeed = self.getSettingValueByKey("retraction_speed") * 60
        recoverlength = round(self.getSettingValueByKey("recover_length"),2)
        recoverspeed = self.getSettingValueByKey("recover_speed") * 60
        if self.getSettingValueByKey("z_hop"):
            hopz = round(self.getSettingValueByKey("zhop_heigth"),1)
        else:
            hopz = 0
        maxiumlayer = self.getSettingValueByKey("maxium_layer")
        
        bAntiscratch_type = 0
        if self.getSettingValueByKey("anti_scratch"):
            if self.getSettingValueByKey("retract_type") == "strong":
                bAntiscratch_type = 2
            else:
                bAntiscratch_type = 1     

        #logo_file = open("d:/output.gcode", "w+")
        #logo_file.write(";;; This file is created by ZONESTAR Color Switch Tower Genaration V1.0.1b\n")
        #logo_file.write(";;; Website: https://zonestar3d.com\n")
        #logo_file.write(";\n")
        
        bFindM109 = 0
        bFindM104 = 0
        bfisrtTx = 1
        bHasPattern = 0
        bNeedAntiscratch = 0
        bRetracted = 0
        
        oldExtrID = -1
        curExtrID = -1
        SwitchingCnt = 0
        backup_e = 0
        
        oldlayer = 0
        curlayer = -1
        totallayers = 99999
        retract_times = 0
        
        flowfactor = round(((1.75*1.75)/(linewidth*linewidth))*1.2,2)
        wipelength = 5
        
        index = 0
        for layer in data:
            lines = layer.split("\n")
            for line in lines:
                line = line.strip()                
                if len(line) == 0:
                    continue
               
                #logo_file.write(line+"\n")
                if ";FLAVOR:Marlin" in line:
                    addtion_gcode = ""
                    if self.getSettingValueByKey("pattern_type") == "line":
                        addtion_gcode += ";pattern type is Line\n"
                    else:
                        addtion_gcode += ";pattern type is Square\n"
                    addtion_gcode += ";colors = {0:d}\n".format(colors)
                    addtion_gcode += ";line width = {0:.2f} mm\n".format(linewidth)
                    addtion_gcode += ";flowfactor = {0:.2f}\n".format(flowfactor)
                    
                    addtion_gcode += ";start_x = {0:d} mm\n".format(startx)
                    addtion_gcode += ";start_y = {0:d} mm\n".format(starty)
                    addtion_gcode += ";tower length = {0:d}mm\n".format(towerlength)
                    addtion_gcode += ";flow length = {0:d} mm\n".format(flowlength)
                    addtion_gcode += ";print speed = {0:d} mm/min\n".format(printspeed)
                    addtion_gcode += ";speed on first layer = {0:d} mm/min\n".format(speedfirstlayer)
                    
                    if self.getSettingValueByKey("retract_type") == "strong":
                        addtion_gcode += ";Synchronous retract\n"
                        l = retractionlength/3
                        s = retractionspeed/3
                        addtion_gcode += "M207 S{0:.2f} F{1:d} W0 Z0\n".format(l, s)
                        addtion_gcode += "M208 S{0:.2f} F{1:d} W0 R{2:d}\n".format(recoverlength, recoverspeed, s)
                    else:
                        addtion_gcode += ";Retract the previous extruder only\n"
                    addtion_gcode += ";retraction length = {0:.2f} mm\n".format(retractionlength)
                    addtion_gcode += ";retraction speed = {0:d} mm/min\n".format(retractionspeed)
                    addtion_gcode += ";recover length = {0:.2f} mm\n".format(recoverlength)
                    addtion_gcode += ";recover speed = {0:d} mm/min\n".format(recoverspeed)
                    if self.getSettingValueByKey("z_hop"):
                        addtion_gcode += ";Z hop heigth = {0:.2f}\n".format(hopz)
                    if bAntiscratch_type > 0:
                        addtion_gcode += ";Anti filament scratch is Enabled\n"
                    addtion_gcode += ";maxium layers = {0:d} mm\n".format(maxiumlayer)
                    
                    data[index] += addtion_gcode
                    #logo_file.write(addtion_gcode)
                    #logo_file.write(";\n")
                    continue
                    
                """    
                if ";MINX:" in line:
                    substr = line[line.find(";MINX:") + len(";MINX:"):]
                    min_x = round(float(substr),4)
                    addtion_gcode = ";min x={:.4f}\n".format(min_x)
                    data[index] += addtion_gcode
                    #logo_file.write(";got min x = {:.4f}\n".format(min_x))
                    continue
                if ";MINY:" in line:
                    substr = line[line.find(";MINY:") + len(";MINY:"):]
                    min_y = round(float(substr),4)
                    addtion_gcode = ";min y={:.4f}\n".format(min_y)
                    data[index] += addtion_gcode
                    #logo_file.write(";got min y = {:.4f}\n".format(min_y))
                    continue
                if ";MAXX:" in line:
                    substr = line[line.find(";MAXX:") + len(";MAXX:"):]
                    max_x = round(float(substr),4)
                    addtion_gcode = ";max x={:.4f}\n".format(max_x)
                    data[index] += addtion_gcode
                    #logo_file.write(";got max x = {:.4f}\n".format(max_x))
                    continue
                if ";MAXY:" in line:
                    substr = line[line.find(";MAXY:") + len(";MAXY:"):]
                    max_y = round(float(substr),4)
                    addtion_gcode = ";max y={:.4f}\n".format(max_y)
                    data[index] += addtion_gcode
                    #logo_file.write(";got max y = {:.4f}\n".format(max_y))
                    continue
                """
                    
                if ";Layer height:" in line:
                    substr = line[line.find(";Layer height:") + len(";Layer height:"):]
                    layerheight = round(float(substr),2)
                    addtion_gcode = ";Layer height={:.2f}\n".format(layerheight)
                    data[index] += addtion_gcode
                    #logo_file.write(";got total_layers = {:.2f}\n".format(totallayers))
                    continue
                    
                # find total layers
                if ";LAYER_COUNT:" in line:
                    substr = line[line.find(";LAYER_COUNT:") + len(";LAYER_COUNT:"):]
                    totallayers = int(substr)
                    #logo_file.write(";got total_layers = {:d}\n".format(totallayers))
                    if maxiumlayer <= 0:
                        maxiumlayer = totallayers
                    continue
                #
                #M109?
                #set flag when find the first M109, and remove others M109
                if line.startswith("M") and "M109" in line:
                    if bFindM109 == 1 and totallayers - curlayer > 1:
                       #not the first M109 command
                       if self.getSettingValueByKey("remove_M104"):
                           #remove this line
                           data[index] = ";removed by script " + line + "\n"
                           #logo_file.write(";remove a M109\n")
                    bFindM109 = 1
                    continue
                    
                #M104?
                #set flag when find the first M104, and remove others M104
                if line.startswith("M") and "M104" in line and (totallayers - curlayer > 1):
                    if bFindM104 == 1 or bFindM109 == 1:
                        #not the first M104 command                        
                        if self.getSettingValueByKey("remove_M104"):
                            #remove this line
                            data[index] = ";removed by script " + line+ "\n"
                            #logo_file.write(";remove a M104\n")
                    bFindM104 = 1
                    continue
                    
                #backup the position
                if line.startswith("G") and (self.getValue(line, "G") == 1 or self.getValue(line, "G") == 0):
                    if (self.getValue(line, "E") is not None) and (self.getValue(line, "G") == 1):
                        provious_e = backup_e
                        backup_e = float(self.getValue(line, "E"))
                        #logo_file.write(";backup_e = {:.5f}\n".format(backup_e))
                        if backup_e < 0 or backup_e < provious_e:
                            retract_times += 1
                            bRetracted = 1
                        else:
                            bRetracted = 0
                    if self.getValue(line, "X") is not None:
                        backup_x = float(self.getValue(line, "X"))
                        #logo_file.write(";backup_x = {:.5f}\n".format(backup_x))
                    if self.getValue(line, "Y") is not None:
                        backup_y = float(self.getValue(line, "Y"))
                        #logo_file.write(";backup_y = {:.5f}\n".format(backup_y))
                    if self.getValue(line, "Z") is not None:
                        backup_z = float(self.getValue(line, "Z"))
                        #logo_file.write(";backup_y = {:.2f}\n".format(backup_z))
                    continue
                        
                if line.startswith("G") and (self.getValue(line, "G") == 92):
                    provious_e = backup_e
                    backup_e = float(self.getValue(line, "E"))
                    continue
                
                # add tower line when layer changed
                if ";LAYER:" in line:   
                    substr = line[line.find(";LAYER:") + len(";LAYER:"):]
                    curlayer = int(substr)
                    #logo_file.write(";got curlayer={:d}\n".format(curlayer))
                    SwitchingCnt = 0
                    if curlayer - oldlayer > 0:
                        #logo_file.write(";ready to add tower\n")                        
                        oldlayer = curlayer
                        if bHasPattern == 1 or curlayer > maxiumlayer:
                            #alread has a pattern, don't make it again
                            bHasPattern = 0
                            continue
                        else:
                            #need to add a patteren
                            #bHasPattern = 1
                            #================================================================
                            # prepare data
                            #================================================================
                            #logo_file.write(";current E = {:.5f}\n".format(backup_e))
                            addtion_gcode = ";Start of tower for layer switching, generated by colorSwitchTower\n"
                            if self.getSettingValueByKey("pattern_type") == "line":
                                n = flowlength*flowfactor/(2*towerlength + 2*colors*linewidth)
                                if (int(n*100)%100) >= 10:
                                   k = int(n+1)
                                else:
                                   k = int(n)
                                p_width = k * 2 * colors * linewidth
                            else:
                                p_width = towerlength
                            #small p-gap in the first layer
                            if curlayer <= 1:
                                p_gap = linewidth*1.2
                            else:
                                #p_gap = (p_width * towerlength) /(flowlength*flowfactor -p_width-towerlength)
                                p_gap = linewidth*5
                            cur_x = startx
                            cur_y = starty
                            addtion_gcode += ";width = {0:.3f}, gap = {1:.3f}\n".format(p_width,p_gap)
                            data[index] += addtion_gcode
                            #================================================================
                            #add retration gcode, before go to the tower 
                            #================================================================
                            #Retraction
                            retract_times += 1
                            addtion_gcode = ""
                            addtion_gcode += ";Retraction\n"
                            if self.getSettingValueByKey("retract_type") == "strong":
                                addtion_gcode += "G92 E0\nG10\n"
                            elif bRetracted == 0:
                                addtion_gcode += "G92 E0\nG1 E-{0:.4f} F{1:d}\n".format(retractionlength, retractionspeed)
                            #z hop
                            if self.getSettingValueByKey("z_hop"):
                                addtion_gcode += ";z hop\n"                            
                                cur_z = backup_z + hopz
                                addtion_gcode += "G1 F360 Z{:.2f}\n".format(cur_z)
                            addtion_gcode += "G0 F6000 X{0:.3f} Y{1:.3f}\n".format(cur_x,cur_y)
                            cur_z = backup_z-layerheight
                            addtion_gcode += "G1 F360 Z{:.2f}\n".format(cur_z)
                            #Recover
                            addtion_gcode += ";Recover\n"
                            recover_e = retractionlength + recoverlength
                            if self.getSettingValueByKey("retract_type") == "strong":
                                addtion_gcode += "G11\nG92 E0\n"
                            else:
                                addtion_gcode += "G92 E0\nG1 E{0:.4f} F{1:d}\nG92 E0\n".format(recover_e,recoverspeed)
                            if curlayer > 1:
                                addtion_gcode += "G1 F{:d}\n".format(printspeed)
                            else:
                                addtion_gcode += "G1 F{:d}\n".format(speedfirstlayer)
                            data[index] += addtion_gcode
                            #logo_file.write(addtion_gcode)
                            #================================================================
                            #Genarate tower
                            #================================================================
                            addtion_gcode = ""
                            addtion_gcode += ";Genarate tower\n"
                            if bAntiscratch_type == 1 and retract_times > 10:
                                retract_times = 0
                                addtion_gcode += "T17\n"
                                bNeedAntiscratch = 1
                            data[index] += addtion_gcode
                            #logo_file.write(addtion_gcode)
                            cur_e = 0.0
                            for i in range(0, 100):
                                addtion_gcode = ""
                                if bAntiscratch_type == 1 and bNeedAntiscratch == 1 and i > 4:
                                    bNeedAntiscratch = 0
                                    if curExtrID < 0:
                                        addtion_gcode += "T0\n"
                                    else:
                                        addtion_gcode += "T{:d}\n".format(curExtrID)
                                #1 Y+
                                old_y = cur_y
                                old_x = cur_x
                                cur_y += p_width
                                cur_e += p_width/flowfactor
                                addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f}\n".format(cur_x,cur_y,cur_e)
                                #2 X+
                                if cur_x >= startx + towerlength - linewidth:
                                    data[index] += addtion_gcode
                                    #logo_file.write(addtion_gcode)
                                    break
                                elif curlayer > 1 and cur_x >= startx + towerlength - p_gap:
                                    cur_x += linewidth
                                    addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f}\n".format(cur_x,cur_y,cur_e)
                                else:
                                    cur_x += p_gap
                                    cur_e += p_gap/flowfactor
                                    addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f}\n".format(cur_x,cur_y,cur_e)
                                #3 Y-
                                old_y = cur_y
                                old_x = cur_x
                                cur_y -= p_width
                                cur_e += p_width/flowfactor
                                addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f}\n".format(cur_x,cur_y,cur_e)                                
                                #4 X+
                                if cur_x >= startx + towerlength - linewidth:
                                    data[index] += addtion_gcode
                                    #logo_file.write(addtion_gcode)
                                    break
                                elif curlayer > 1 and cur_x >= startx + towerlength - p_gap:
                                    cur_x += linewidth
                                    addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f}\n".format(cur_x,cur_y,cur_e)
                                else:
                                    cur_x += p_gap
                                    cur_e += p_gap/flowfactor
                                    addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f}\n".format(cur_x,cur_y,cur_e)
                                data[index] += addtion_gcode
                                #logo_file.write(addtion_gcode)
                            #================================================================
                            #restore the extruder length
                            #================================================================
                            addtion_gcode = ""
                            #retract
                            retract_times += 1
                            addtion_gcode += ";retract\n"
                            if self.getSettingValueByKey("retract_type") == "strong":
                                addtion_gcode += "G92 E0\nG10\n"
                            else:
                                addtion_gcode += "G92 E0\nG1 E-{0:.3f} F{1:d}\n".format(retractionlength,retractionspeed)
                            #wipe nozzle
                            addtion_gcode += ";wipe nozzle\n"
                            addtion_gcode +=  "G0 F3000 X{0:.3f} Y{1:.3f}\n".format(old_x, old_y)
                            #Z hop and go to 
                            if self.getSettingValueByKey("z_hop"):
                                addtion_gcode += ";Z hop and leave the tower\n"
                                cur_z = backup_z + hopz
                                addtion_gcode += "G1 F360 Z{:.2f}\n".format(cur_z)
                            addtion_gcode += "G0 F6000 X{0:.3f} Y{1:.3f}\n".format(backup_x,backup_y)
                            addtion_gcode += "G1 F360 Z{:.2f}\n".format(backup_z)
                            #recover
                            addtion_gcode += ";recover\n"
                            recover_e = retractionlength + recoverlength
                            if self.getSettingValueByKey("retract_type") == "strong":
                                addtion_gcode += "G11\n"
                            elif bRetracted == 0:
                                addtion_gcode += "G92 E0\nG1 E{0:.4f} F{1:d}\n".format(recover_e,recoverspeed)
                            #resume e
                            addtion_gcode += "G92 E{:.5f}\n".format(backup_e)
                            addtion_gcode += ";End of Tower for layer switching, generated by colorSwitchTower\n\n"
                            data[index] += addtion_gcode
                            #logo_file.write(addtion_gcode)
                            continue
                        #
                    #
                #
                #add tower when color changed
                #find Tx command and add command
                if line.startswith("T") and (self.getValue(line, "T") is not None) and curlayer >= 0:                    
                    curExtrID = self.getValue(line, "T")
                    #logo_file.write(";got T{:d}\n".format(curExtrID))
                    if curExtrID > 7:
                        continue
                    #Ignore the first Tx command
                    if oldExtrID < 0: #the fist tool chain setting command, don't make patterent
                        oldExtrID = curExtrID
                        #logo_file.write(";Pass the first one Tx\n")
                        continue
                    #logo_file.write(";ready to add tower\n")
                    #make patterent
                    bHasPattern = 1
                    #================================================================
                    #add retration gcode before go to the tower 
                    #================================================================                           
                    recover_e = retractionlength + recoverlength
                    addtion_gcode = ";Start of tower for toolchain change, generated by colorSwitchTower\n"
                    #retract
                    retract_times += 1
                    addtion_gcode += ";retract\n"
                    if self.getSettingValueByKey("retract_type") == "strong":
                        addtion_gcode += "G92 E0\nG10\n"
                    else:
                        if self.getSettingValueByKey("retract_type") == "enhanced" and bRetracted == 0:
                            addtion_gcode += "T{:d}\n".format(oldExtrID)
                            addtion_gcode += "G92 E0\nG1 E-{0:.3f} F{1:d}\n".format(retractionlength,retractionspeed)
                        if self.getSettingValueByKey("retract_type") == "enhanced":
                            addtion_gcode += "T{:d}\n".format(curExtrID)
                        addtion_gcode += "G92 E0\nG1 E-{0:.3f} F{1:d}\n".format(retractionlength,retractionspeed)
                    #Z Hop and goto
                    if self.getSettingValueByKey("z_hop"):
                        cur_z = backup_z + hopz
                        addtion_gcode += ";Z hop\n"
                        addtion_gcode += "G1 F360 Z{0:.2f}\n".format(cur_z)
                    addtion_gcode += "G0 F6000 X{0:.3f} Y{1:.3f}\n".format(startx,starty)
                    if self.getSettingValueByKey("z_hop"):
                        addtion_gcode += "G1 F360 Z{:.2f}\n".format(backup_z)
                    #Recover
                    addtion_gcode += ";Recover\n"
                    if self.getSettingValueByKey("retract_type") == "strong":
                        addtion_gcode += "G92 E0\nG11\n"
                    else:
                        if self.getSettingValueByKey("retract_type") == "enhanced" and bRetracted == 0:
                            addtion_gcode += "T{:d}\n".format(oldExtrID)
                            addtion_gcode += "G92 E0\nG1 E{0:.4f} F{1:d}\n".format(recover_e,recoverspeed)
                        if self.getSettingValueByKey("retract_type") == "enhanced":
                            addtion_gcode += "T{:d}\n".format(curExtrID)
                        addtion_gcode += "G92 E0\nG1 E{0:.4f} F{1:d}\nG92 E0\n".format(recover_e,recoverspeed)
                    #done
                    data[index] += addtion_gcode
                    #logo_file.write(addtion_gcode)
                    #================================================================
                    #Genarate tower gcode
                    #================================================================
                    if curlayer <= 1:
                        movementspeed = speedfirstlayer
                    else:
                        movementspeed = printspeed
                    if self.getSettingValueByKey("pattern_type") == "line":
                        addtion_gcode = ""
                        addtion_gcode += ";Line tower\n"
                        cur_x = startx
                        cur_y = starty
                        #sync clean tower on the first
                        if bAntiscratch_type == 1 and retract_times > 10:
                            retract_times = 0
                            addtion_gcode += ";anti scratch\n"
                            addtion_gcode += "T17\nG92 E0\n"
                            bNeedAntiscratch = 1
                        elif bAntiscratch_type == 2:
                            addtion_gcode += ";anti scratch\n"
                            addtion_gcode += "T17\nG92 E0\n"
                            cur_e = 0
                            for i in range(0, 3):
                                cur_x += towerlength
                                cur_e += towerlength/flowfactor
                                addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f} F{3:d}\n".format(cur_x,cur_y,cur_e,movementspeed)
                                cur_y += linewidth
                                addtion_gcode += "G0 Y{0:.3f} F{1:d}\n".format(cur_y,movementspeed)
                                cur_x -= towerlength
                                cur_e += towerlength/flowfactor
                                addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f} F{3:d}\n".format(cur_x,cur_y,cur_e,movementspeed)
                                cur_y += linewidth
                                addtion_gcode += "G0 Y{0:.3f} F{1:d}\n".format(cur_y,movementspeed)
                            addtion_gcode += "T{:d}\nG92 E0\n".format(curExtrID)
                        data[index] += addtion_gcode          
                        #
                        cur_x -= SwitchingCnt * linewidth
                        cur_y += SwitchingCnt * linewidth
                        cur_e = 0
                        addtion_gcode = ""
                        addtion_gcode += ";line tower start\n"
                        addtion_gcode += "G0 X{0:.3f} Y{1:.3f} F6000\n".format(cur_x,cur_y)
                        data[index] += addtion_gcode
                        #logo_file.write(addtion_gcode)
                        for i in range(0, 100):
                            addtion_gcode = ""
                            if bAntiscratch_type == 1 and bNeedAntiscratch == 1 and i > 2:
                                    bNeedAntiscratch = 0
                                    if curExtrID < 0:
                                        addtion_gcode += "T0\n"
                                    else:
                                        addtion_gcode += "T{:d}\n".format(curExtrID)
                            #1 X+
                            cur_x += towerlength
                            cur_e += towerlength/flowfactor
                            addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f} F{3:d}\n".format(cur_x,cur_y,cur_e,movementspeed)
                            #2 Y+
                            cur_y += ((colors - SwitchingCnt)*2 -1)*linewidth
                            cur_e += ((colors - SwitchingCnt)*2 -1)*linewidth/flowfactor
                            addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f} F{3:d}\n".format(cur_x,cur_y,cur_e,speedfirstlayer)
                            #3 X-
                            if (cur_e <= (flowlength - towerlength/(flowfactor*2))):
                                cur_x -= towerlength
                                cur_e += towerlength/flowfactor
                                addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f} F{3:d}\n".format(cur_x,cur_y,cur_e,movementspeed)
                            else:
                                cur_x -= (towerlength - wipelength)
                                cur_e += (towerlength - wipelength)/flowfactor
                                addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f} F{3:d}\n".format(cur_x,cur_y,cur_e,movementspeed)
                                cur_x -= wipelength
                                addtion_gcode += "G0 X{0:.3f} Y{1:.3f} F{2:d}\n".format(cur_x,cur_y,movementspeed)
                                data[index] += addtion_gcode
                                #logo_file.write(addtion_gcode)
                                break
                            #4 Y+
                            cur_y += (SwitchingCnt*2 + 1)*linewidth
                            cur_e += (SwitchingCnt*2 + 1)*linewidth/flowfactor
                            addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f} F{3:d}\n".format(cur_x,cur_y,cur_e,movementspeed)
                            data[index] += addtion_gcode
                            #logo_file.write(addtion_gcode)                            
                    else:
                        addtion_gcode = ""
                        addtion_gcode += ";square tower\n"
                        if bAntiscratch_type == 1 and retract_times > 10:
                            retract_times = 0
                            addtion_gcode += ";anti scratch\n"
                            addtion_gcode += "T17\nG92 E0\n"
                            bNeedAntiscratch = 1
                        elif bAntiscratch_type == 2:
                            addtion_gcode += ";anti scratch\n"
                            addtion_gcode += "T17\nG92 E0\n"
                            cur_e = 0
                            for i in range(0, 2):
                                cur_x = startx - 2*linewidth + i*linewidth
                                cur_y = starty - 2*linewidth + i*linewidth
                                move_length = towerlength + 4*linewidth - 2*i*linewidth
                                cur_x += move_length
                                cur_e += move_length/flowfactor
                                addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f} F{3:d}\n".format(cur_x,cur_y,cur_e,movementspeed)
                                cur_y += move_length
                                cur_e += move_length/flowfactor
                                addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f} F{3:d}\n".format(cur_x,cur_y,cur_e,movementspeed)
                                cur_x -= move_length
                                cur_e += move_length/flowfactor
                                addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f} F{3:d}\n".format(cur_x,cur_y,cur_e,movementspeed)
                                cur_y -= move_length
                                cur_e += move_length/flowfactor
                                addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f} F{3:d}\n".format(cur_x,cur_y,cur_e,movementspeed)
                            addtion_gcode += "T{:d}\nG92 E0\n".format(curExtrID)
                        data[index] += addtion_gcode       
                        #
                        addtion_gcode = ""
                        addtion_gcode += ";square tower start\n"
                        data[index] += addtion_gcode
                        #logo_file.write(addtion_gcode)
                        cur_e = 0.0
                        #logo_file.write(addtion_gcode)
                        for i in range(0, 1000):
                            addtion_gcode = ""
                            if bAntiscratch_type == 1 and bNeedAntiscratch == 1 and i > 1:
                                bNeedAntiscratch = 0
                                if curExtrID < 0:
                                    addtion_gcode += "T0\n"
                                else:
                                    addtion_gcode += "T{:d}\n".format(curExtrID)
                            cur_x = float(startx + (SwitchingCnt * linewidth) + (i * linewidth * colors))
                            cur_y = float(starty + (SwitchingCnt * linewidth) + (i * linewidth * colors))
                            move_length = float(towerlength - SwitchingCnt * linewidth * 2 - i * linewidth * colors * 2)
                            if move_length <= 6:
                                break
                            #goto to the start position
                            addtion_gcode += "G0 F6000 X{0:.3f} Y{1:.3f}\n".format(cur_x, cur_y)
                            addtion_gcode += "G1 F{:d}\n".format(movementspeed)
                            #x+
                            cur_x += move_length
                            cur_e += move_length/flowfactor
                            addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f}\n".format(cur_x, cur_y, cur_e)
                            #Y+
                            cur_y += move_length
                            cur_e += move_length/flowfactor
                            addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f}\n".format(cur_x, cur_y, cur_e)
                            #x-
                            cur_x -= move_length
                            cur_e += move_length/flowfactor
                            addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f}\n".format(cur_x, cur_y, cur_e)
                            #Y-
                            if(cur_e >= flowlength) or (move_length <= 6):
                                cur_y -= (move_length-wipelength)
                                cur_e += (move_length-wipelength)/flowfactor
                                addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f}\n".format(cur_x, cur_y, cur_e)
                                cur_y -= wipelength
                                addtion_gcode += "G0 X{0:.3f} Y{1:.3f} \n".format(cur_x, cur_y)
                                cur_x = float(startx + (SwitchingCnt * linewidth))
                                cur_y = float(starty + (SwitchingCnt * linewidth) + towerlength)
                                addtion_gcode += "G0 X{0:.3f} Y{1:.3f} \n".format(cur_x, cur_y)
                                data[index] += addtion_gcode
                                #logo_file.write(addtion_gcode)
                                break
                            else:
                                cur_y -= move_length
                                cur_e += move_length/flowfactor
                                addtion_gcode += "G1 X{0:.3f} Y{1:.3f} E{2:.4f}\n".format(cur_x, cur_y, cur_e)
                                data[index] += addtion_gcode
                                #logo_file.write(addtion_gcode)
                    #================================================================
                    #retration before leave the tower
                    #================================================================
                    addtion_gcode = ""
                    addtion_gcode += ";leave the tower\n"
                    addtion_gcode += "G92 E0\n"
                    #retract
                    addtion_gcode += ";Retract\n"
                    if self.getSettingValueByKey("retract_type") == "strong":
                        addtion_gcode += "G10\n"
                    else:
                        if self.getSettingValueByKey("retract_type") == "enhanced" and bRetracted == 0:
                            addtion_gcode += "T{:d}\n".format(oldExtrID)
                            addtion_gcode += "G92 E0\nG1 E-{0:.3f} F{1:d}\n".format(retractionlength,retractionspeed)
                        if self.getSettingValueByKey("retract_type") == "enhanced":
                            addtion_gcode += "T{:d}\n".format(curExtrID)
                        addtion_gcode += "G92 E0\nG1 E-{0:.3f} F{1:d}\n".format(retractionlength,retractionspeed)
                    #wipe nozzle
                    addtion_gcode += ";wipe nozzle\n"
                    if self.getSettingValueByKey("pattern_type") == "line":
                        cur_x += towerlength
                        addtion_gcode += "G0 F3000 X{0:.3f} Y{1:.3f}\n".format(cur_x, cur_y)
                    else:
                        addtion_gcode += "G0 F3000 X{0:.3f} Y{1:.3f}\n".format(startx, starty)
                    #Z hop and move back
                    if self.getSettingValueByKey("z_hop"):
                        addtion_gcode += ";Z hop\n"
                        cur_z = backup_z + hopz
                        addtion_gcode += "G1 F360 Z{:.2f}\n".format(cur_z)
                    addtion_gcode += "G0 F6000 X{0:.3f} Y{1:.3f}\n".format(backup_x, backup_y)
                    if self.getSettingValueByKey("z_hop"):
                        addtion_gcode += "G1 F360 Z{:.2f}\n".format(backup_z)
                    #Recover
                    recover_e = retractionlength + recoverlength
                    addtion_gcode += ";Recover\n"
                    if self.getSettingValueByKey("retract_type") == "strong":
                        addtion_gcode += "G92 E0\nG11\n"
                        addtion_gcode += "T{:d}\n".format(curExtrID)
                    else:
                        if self.getSettingValueByKey("retract_type") == "enhanced" and bRetracted == 0:
                            addtion_gcode += "T{:d}\n".format(oldExtrID)
                            addtion_gcode += "G92 E0\nG1 E{0:.3f} F{1:d}\n".format(recover_e,recoverspeed)
                        if self.getSettingValueByKey("retract_type") == "enhanced":
                            addtion_gcode += "T{:d}\n".format(curExtrID)
                        addtion_gcode += "G92 E0\nG1 E{0:.3f} F{1:d}\n".format(recover_e,recoverspeed)
                    addtion_gcode += "G92 E0\n"
                    addtion_gcode += ";End of tower for toolchain change, generated by colorSwitchTower\n\n"
                    data[index] += addtion_gcode
                    #logo_file.write(addtion_gcode)
                    #refersh old extustion, must be here!!!!
                    oldExtrID = curExtrID
                    #bRetracted = 0
                    SwitchingCnt += 1
                    continue
                #Tn
            #for line
            index += 1
        #for layer
        #logo_file.close()
        return data
