# Copyright (c) 2021 Mike de Klerk
# The PostProcessingPlugin is released under the terms of the AGPLv3 or higher.

from ..Script import Script
import re
import json

class MultilayerBrimProcessor:

    layerCount = None
    nrOfLayers = None

    def __init__(self):
        self.layerCount = 0

    def changeLineParameter(self, newLine, parameter, multiplier, offset):
        pattern = " " + parameter
        flt = None
        newFlt = None
        if newLine.find(pattern) != -1:
            lineSplit = newLine.split(pattern)
            flt = float(lineSplit[1])
            newFlt = (flt * multiplier) + offset
            newFlt = round(newFlt, 5)
            newLine = lineSplit[0] + pattern + str(newFlt)
        return (newLine, flt, newFlt)

    def multilayer(self, gcodeSnippet, multiplier, extrusionOffset):
        print('mp: ' + str(multiplier) + ", extrusionOffset: " + str(extrusionOffset))
        lines = gcodeSnippet.split("\n")
        newLines = []
        zWasChanged = False
        lastExtrusionValue = 0
        lastOriEValue = 0
        for line in lines:
            newLine = line

            # Change height of layer
            if not zWasChanged:
                (newLine, oriZValue, newZValue) = self.changeLineParameter(newLine, "Z", multiplier, 0)

            # Change extrusion
            if newLine.find(" E") != -1:
                (newLine, lastOriEValue, lastExtrusionValue) = self.changeLineParameter(newLine, "E", 1 / self.nrOfLayers, extrusionOffset)

            newLines.append(newLine)

        newGcodeSnippet = ""
        for l in newLines:
            newGcodeSnippet = newGcodeSnippet + l + "\n"
        print("lastOriEValue: " + str(lastOriEValue))
        return (newGcodeSnippet, lastExtrusionValue)

    def setLayerCount(self, gcodeSnippet):
        gcodeSnippet = re.sub(
            ";LAYER:[0-9]+", ";LAYER:" + str(self.layerCount), gcodeSnippet, 1)
        self.layerCount = self.layerCount + 1
        return gcodeSnippet

    def process(self, gcodeSnippet, nrOfLayers):
        self.nrOfLayers = nrOfLayers
        if gcodeSnippet.find(";LAYER:0") == -1:
            if gcodeSnippet.find(";LAYER:") != -1:
                gcodeSnippet = self.setLayerCount(gcodeSnippet)
            return gcodeSnippet

        mpUnit = 1 / nrOfLayers
        (newData, lastExtrusionValue) = self.multilayer(gcodeSnippet, 1 / nrOfLayers, 0)
        newData = self.setLayerCount(newData)
        finalSnippet = newData
        for i in range(1, nrOfLayers):
            mp = mpUnit + (i * mpUnit)
            (layerData, lastExtrusionValue) = self.multilayer(gcodeSnippet, mp, lastExtrusionValue)
            layerData = self.setLayerCount(layerData)
            layerData = self.commentZeroFeeder(layerData)
            finalSnippet = finalSnippet + layerData

        return finalSnippet

    def commentZeroFeeder(self, gcodeSnippet):
        return re.sub("G1\sF[0-9]+\sE0\.0", "; Removed zeroing of feeder", gcodeSnippet, 1)

    def processLayers(self, layers, nrOfLayers):
        self.layerCount = 0
        newLayers = []
        for layer_number, layer in enumerate(layers):
            gcodeSnippet = self.process(layer, nrOfLayers)
            newLayers.append(gcodeSnippet)
        return newLayers


class MultilayerBrim(Script):
    """Turns the single layer brim into a multi-layer brim respecting the original height.
    The idea behind having multiple thinner layers for the brim is to increase the adhesion and thereby reduce warping. Especially for ABS parts.
    """
    processor = None

    def __init__(self):
        self.processor = MultilayerBrimProcessor()

    def getSettingDataString(self):
        return """{
            "name": "Multilayer brim",
            "key": "MultilayerBrim",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "nrOfLayers":
                {
                    "label": "Number of layers",
                    "description": "The brim will be printed in this number of layers.",
                    "type": "int",
                    "default_value": "2"
                }
            }
        }"""

    def execute(self, data):
        nrOfLayers = self.getSettingValueByKey("nrOfLayers")
        return self.processor.processLayers(data, nrOfLayers)
