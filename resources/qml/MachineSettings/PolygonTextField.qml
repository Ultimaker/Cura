// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// TextField for editing polygon data in the Machine Settings dialog.
//
UM.TooltipArea
{
    UM.I18nCatalog { id: catalog; name: "cura"; }

    height: textField.height
    width: textField.width
    text: tooltip

    property alias containerStackId: propertyProvider.containerStackId
    property alias settingKey: propertyProvider.key
    property alias settingStoreIndex: propertyProvider.storeIndex

    property alias labelText: fieldLabel.text
    property alias labelWidth: fieldLabel.width
    property string unitText: catalog.i18nc("@label", "mm")

    // callback functions
    property var forceUpdateOnChangeFunction: dummy_func

    // a dummy function for default property values
    function dummy_func() {}

    property var printHeadPolygon:
    {
        "x": {
            "min": 0,
            "max": 0,
        },
        "y": {
            "min": 0,
            "max": 0,
        },
    }

    UM.SettingPropertyProvider
    {
        id: propertyProvider
        watchedProperties: [ "value" ]
    }

    Row
    {
        spacing: UM.Theme.getSize("default_margin").width

        Label
        {
            id: fieldLabel
            anchors.verticalCenter: textFieldWithUnit.verticalCenter
            visible: text != ""
            elide: Text.ElideRight
            //width: Math.max(0, settingsTabs.labelColumnWidth)
        }

        Item
        {
            id: textFieldWithUnit
            width: textField.width
            height: textField.height

            TextField
            {
                id: textField
                text:
                {
                    var polygon = JSON.parse(propertyProvider.properties.value)
                    var item = (axis == "x") ? 0 : 1
                    var result = polygon[0][item]
                    for (var i = 1; i < polygon.length; i++) {
                        result = (side == "min")
                                 ? Math.min(result, polygon[i][item])
                                 : Math.max(result, polygon[i][item])
                    }
                    result = Math.abs(result)
                    printHeadPolygon[axis][side] = result
                    return result
                }
                validator: RegExpValidator { regExp: /[0-9\.,]{0,6}/ }
                onEditingFinished:
                {
                    printHeadPolygon[axis][side] = parseFloat(textField.text.replace(',','.'))
                    var polygon = [
                        [-printHeadPolygon["x"]["min"],  printHeadPolygon["y"]["max"]],
                        [-printHeadPolygon["x"]["min"], -printHeadPolygon["y"]["min"]],
                        [ printHeadPolygon["x"]["max"],  printHeadPolygon["y"]["max"]],
                        [ printHeadPolygon["x"]["max"], -printHeadPolygon["y"]["min"]]
                    ]
                    var polygon_string = JSON.stringify(polygon)
                    if (polygon_string != propertyProvider.properties.value)
                    {
                        propertyProvider.setPropertyValue("value", polygon_string)
                        forceUpdateOnChangeFunction()
                    }
                }
            }

            Label
            {
                id: unitLabel
                text: unitText
                anchors.right: textField.right
                anchors.rightMargin: y - textField.y
                anchors.verticalCenter: textField.verticalCenter
            }
        }
    }
}
