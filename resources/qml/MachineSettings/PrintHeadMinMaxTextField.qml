// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This is the widget for editing min and max X and Y for the print head.
// The print head is internally stored as a JSON array or array, representing a polygon of the print head.
// The polygon array is stored in the format illustrated below:
//      [  [ -x_min,  y_max ],
//         [ -x_min, -y_min ],
//         [  x_max,  y_max ],
//         [  x_max, -y_min ],
//       ]
//
// In order to modify each field, the widget is configurable via "axisName" and "axisMinOrMax", where
//     - axisName is "x" or "y"
//     - axisMinOrMax is "min" or "max"
//
NumericTextFieldWithUnit
{
    id: machineXMaxField
    UM.I18nCatalog { id: catalog; name: "cura" }

    containerStackId: Cura.MachineManager.activeMachineId
    settingKey: "machine_head_with_fans_polygon"
    settingStoreIndex: 1

    property string axisName: "x"
    property string axisMinOrMax: "min"
    property var axisValue:
    {
        var polygon = JSON.parse(propertyProvider.properties.value)
        var item = (axisName == "x") ? 0 : 1
        var result = polygon[0][item]
        var func = (axisMinOrMax == "min") ? Math.min : Math.max
        for (var i = 1; i < polygon.length; i++)
        {
            result = func(result, polygon[i][item])
        }
        result = Math.abs(result)
        return result
    }

    valueValidator: RegExpValidator { regExp: /[0-9\.,]{0,6}/ }
    valueText: axisValue

    editingFinishedFunction: function()
    {
        var polygon = JSON.parse(propertyProvider.properties.value)

        var newValue = parseFloat(valueText.replace(',', '.'))
        if (axisName == "x")  // x min/x max
        {
            var start_i1 = (axisMinOrMax == "min") ? 0 : 2
            var factor = (axisMinOrMax == "min") ? -1 : 1
            polygon[start_i1][0] = newValue * factor
            polygon[start_i1 + 1][0] = newValue * factor
        }
        else  // y min/y max
        {
            var start_i1 = (axisMinOrMax == "min") ? 1 : 0
            var factor = (axisMinOrMax == "min") ? -1 : 1
            polygon[start_i1][1] = newValue * factor
            polygon[start_i1 + 2][1] = newValue * factor
        }
        var polygon_string = JSON.stringify(polygon)
        if (polygon_string != propertyProvider.properties.value)
        {
            propertyProvider.setPropertyValue("value", polygon_string)
            forceUpdateOnChangeFunction()
        }
    }
}
