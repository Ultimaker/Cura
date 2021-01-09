# ColorMix_goofoo extruder color mix and blending
# This script is specific for the goofoo dual extruder. 
# -*- coding: UTF-8 -*-

import re #To perform the search and replace.
from ..Script import Script

class ColorMix_goofoo(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"ColorMix 2-1 goofoo",
            "key":"ColorMix_goofoo",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "units_of_measurement":
                {
                    "label": "Units",
                    "description": "Input value as mm or layer number.",
                    "type": "enum",
                    "options": {"mm":"mm","layer":"Layer"},
                    "default_value": "layer"
                },
                "start_height":
                {
                    "label": "Start Height",
                    "description": "Value to start at (mm or layer)",
                    "type": "float",
                    "default_value": 0,
                    "minimum_value": "0"
                },
                "behavior":
                {
                    "label": "Fixed or blend",
                    "description": "Select Fixed (set new mixture) or Blend mode (dynamic mix)",
                    "type": "enum",
                    "options": {"fixed_value":"Fixed","blend_value":"Blend"},
                    "default_value": "fixed_value"
                },
                "mix_radio":
                {
                    "label": "mix ratio",
                    "description": "First extruder percentage 5-95",
                    "type": "int",
                    "default_value": 95,
                    "minimum_value": "5",
                    "minimum_value_warning": "5",
                    "maximum_value_warning": "95"
                }
            }
        }"""
    def getValue(self, line, key, default = None): #replace default getvalue due to comment-reading feature
        if not key in line:
            return default
        subPart = line[line.find(key) + len(key):] #allows for string lengths larger than 1
        if ";ChangeAtZ" in key:
            m = re.search("^[0-4]", subPart)
        elif ";LAYER:" in key:
            m = re.search("^[+-]?[0-9]*", subPart)
        elif ";LAYER_COUNT:" in key:
            m = re.search("[0-9]*", subPart)
        else:
            #the minus at the beginning allows for negative values, e.g. for delta printers
            m = re.search("^[-]?[0-9]*\.?[0-9]*", subPart)
        if m == None:
            return default
        try:
            return float(m.group(0))
        except:
            return default 
    def analyData(self,data,layerObjs,setObj):
        for active_layer in data:
            lines = active_layer.split("\n")
            for line in lines:#;GOOFOO_2-1:sRatio:5 fixed:1 layer 5
                if ";GOOFOO_2-1:" in line:#checks for state change comment
                    layerObjs.append({'sRatio':int(self.getValue(line,"sRatio",0)),'fixed':int(self.getValue(line,"fixed",1)),'layer':int(self.getValue(line,"layer",0)),'isUse':0})
    def findItem(self,layerObjs,idx):
        if None == layerObjs:
            return None
        arrCount = len(layerObjs)
        if arrCount <= 0:
            return None
        itemObj = None
        for i in range(arrCount):
            itemObj = layerObjs[i]
            if int(idx) == int(itemObj['layer']):
                return itemObj
        return None
    def getSetObj(self,setObj,data,layerObjs):
        sHei = self.getSettingValueByKey("start_height")
        sMix = int(self.getSettingValueByKey("mix_radio"))
        sMix = 100 - sMix
        setObj['sRatio'] = sMix
        isFixed = 0
        if "fixed_value" == self.getSettingValueByKey("behavior"):
            isFixed = 1
        setObj['fixed'] = isFixed

        isMMType = 0
        if "mm" == self.getSettingValueByKey("units_of_measurement"):
            isMMType = 1
        
        layerHeight = 0
        for active_layer in data:
            lines = active_layer.split("\n")
            for line in lines:
                if ";Layer height: " in line:
                    layerHeight = self.getValue(line,";Layer height: ",layerHeight)
                    break
            if layerHeight != 0:
                break
        if 0 == layerHeight:
            layerHeight = .2
        setObj['layerHeight'] = layerHeight
        layerCount = 0
        for active_layer in data:
            lines = active_layer.split("\n")
            for line in lines:
                if ";LAYER_COUNT:" in line:
                    layerCount = int(self.getValue(line,";LAYER_COUNT:",layerCount))
                    break
            if layerCount != 0:
                break
        if 0 == layerCount:
            layerCount = 1
        setObj['layerCount'] = int(layerCount)
        
        if isMMType:
            sHei = round(sHei / layerHeight)
        if sHei < 0:
            sHei = 1 
        startLayer = int(sHei)
        if startLayer > layerCount:
            startLayer = layerCount
            setObj['isSetEnd'] = 1
        setObj['layer'] = startLayer
        
        itemObj = None
        itemObj = self.findItem(layerObjs,startLayer)
        if None == itemObj:
            layerObjs.append({'sRatio':sMix,'incRation':0.0,'fixed':isFixed,'layer':startLayer,'isUse':0})
        else:
            itemObj['sRatio'] = sMix
            itemObj['incRation'] = 0.0
            itemObj['fixed'] = isFixed
            itemObj['isUse'] = 0
    def sortLayer(self,layerObjs,setObj):
        itemObj = None
        itemObj = self.findItem(layerObjs,0)
        if None == itemObj:
            layerObjs.append({'sRatio':100,'fixed':1,'layer':0})
        itemObj = self.findItem(layerObjs,int(setObj['layerCount']))
        if None == itemObj:
            layerObjs.append({'sRatio':0,'fixed':1,'layer':int(setObj['layerCount'])})
        else:
            setObj['isSetEnd'] = 1
    def analyIncRatio(self,layerObjs,setObj):
        if None == layerObjs:
            return None
        layerCount = len(layerObjs)
        if 0 >= layerCount:
            return None
        for i in range(layerCount-1):
            itemObj = layerObjs[i]
            nextObj = layerObjs[i+1]
            if None != itemObj and None != nextObj:
                # or setObj['isSetEnd'] == 1
                if 5 > int(itemObj['sRatio']):
                    itemObj['sRatio'] = 5
                if 95 < int(itemObj['sRatio']):
                    itemObj['sRatio'] = 95
                if 5 > int(nextObj['sRatio']):
                    nextObj['sRatio'] = 5
                if 95 < int(nextObj['sRatio']):
                    nextObj['sRatio'] = 95
                if 0 == itemObj['fixed']:
                    itemObj['incRation'] = float((nextObj['sRatio']-itemObj['sRatio'])/(nextObj['layer']-itemObj['layer']))
                else:
                    itemObj['incRation'] = 0.0
            else:
                itemObj['incRation'] = 0.0
        layerObjs[layerCount-1]['incRation'] = 0.0
    def findLayerInfo(self,layer,layerObjs):
        if int(layer) < 0:
            return None
        if None == layerObjs:
            return None
        layerCount = len(layerObjs)
        if layerCount <= 1:
            return None
        itemObj = None
        for i in range(layerCount-1):
            itemObj = layerObjs[i]
            nextObj = layerObjs[i+1]
            if int(layer) >= int(itemObj['layer']) and int(layer) <= int(nextObj['layer']) and itemObj['isUse'] == 0:
                if(itemObj['fixed'] == 1):
                    itemObj['isUse'] = 1
                return itemObj
        return None
    def createCommand(self,data,layerObjs,setObj):
        index = 0
        layer = -1
        itemObj = None
        isInitMaxHei = 0
        nextLine = ""
        findCount = 0
        curLayer = 0
        start = 0
        for active_layer in data:
            modified_gcode = ""
            lineIndex = 0
            lines = active_layer.split("\n")
            for line in lines:
                #dont leave blanks 
                if ";MAX_Z_HEIGHT:" in line:
                    isInitMaxHei = 1
                if isInitMaxHei == 0:
                    isInitMaxHei = 1
                    modified_gcode = ";MAX_Z_HEIGHT:{0:f}\n".format(float(setObj['layerHeight'] * setObj['layerCount']))
                
                if start == 0 and ";LAYER_COUNT" in line:
                    start = 1
                if start == 1:
                    # if itemObj != None and "G1" in line or "G0" in line and "E" in line:
                    #     modified_gcode += "M6050 S{0:2f} P{1:2f} Z{2:f}\n".format(float(firstExtruderValue/100.0),0.0,float(curHeight))
                    if ("G1" in line or "G0" in line) and "Z" in line:
                        itemObj = self.findLayerInfo(int(curLayer),layerObjs)
                        if None != itemObj:
                            firstExtruderValue = int(((curLayer - itemObj['layer']) * itemObj['incRation']) + itemObj['sRatio'])
                            curHeight = self.getValue(line,"Z",0.0)
                            modified_gcode += "M6050 S{0:2f} P{1:2f} Z{2:f}\n".format(float(firstExtruderValue/100.0),0.0,float(curHeight))
                        curLayer+=1
                if line != "":
                    modified_gcode += line + "\n"
                lineIndex += 1  #for deleting index
            data[index] = modified_gcode
            index += 1
    def delFlag(self,data,layerObjs):
        index = 0
        for active_layer in data:
            # lineIndex = 0
            modified_gcode = ""
            lines = active_layer.split("\n")
            for line in lines:
                if ";GOOFOO_2-1:" not in line and "M6050" not in line and "T0" not in line:
                    modified_gcode += line + "\n"
            data[index] = modified_gcode   
            index += 1  
        isInitFlag = 0
        index = 0
        for active_layer in data:
            modified_gcode = ""
            lines = active_layer.split("\n")
            for line in lines:
                if line != "":
                    modified_gcode += line + "\n"
                if ";GOOFOO_2-1:" in line:
                    isInitFlag = 1
                if isInitFlag == 0:
                    isInitFlag = 1
                    layerCount = len(layerObjs)
                    itemObj = None
                    for i in range(layerCount):
                        itemObj = layerObjs[i]
                        modified_gcode += ";GOOFOO_2-1:sRatio{0:d} fixed{1:d} layer{2:d}\n".format(itemObj['sRatio'],itemObj['fixed'],itemObj['layer'])
            data[index] = modified_gcode   
            index += 1            
    def execute(self, data):
        setObj = {'sRatio':100,'incRation':0,'fixed':1,'layer':0,'layerCount':1,'layerHeight':.2,'isSetEnd':0,"endlayer":1,'eRatio':100,'isUseSet':0}
        layerObjs = []
        self.getSetObj(setObj,data,layerObjs)
        self.analyData(data,layerObjs,setObj)
        self.sortLayer(layerObjs,setObj)
        layerObjs = sorted(layerObjs,key=lambda e:e['layer'])
        self.delFlag(data,layerObjs)
        self.analyIncRatio(layerObjs,setObj)
        self.createCommand(data,layerObjs,setObj)
        return data