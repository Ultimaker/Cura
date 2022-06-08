// Copyright (c) 2020 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.1 as Cura


//
// CheckBox widget for the on/off or true/false settings in the Machine Settings Dialog.
//
UM.TooltipArea
{
    id: simpleCheckBox

    UM.I18nCatalog { id: catalog; name: "cura"; }

    property int controlHeight: UM.Theme.getSize("setting_control").height

    height: controlHeight
    width: childrenRect.width
    text: tooltip

    property alias containerStackId: propertyProvider.containerStackId
    property alias settingKey: propertyProvider.key
    property alias settingStoreIndex: propertyProvider.storeIndex

    property alias labelText: fieldLabel.text
    property alias labelFont: fieldLabel.font
    property alias labelWidth: fieldLabel.width

    property string tooltip: propertyProvider.properties.description ? propertyProvider.properties.description : ""

    // callback functions
    property var forceUpdateOnChangeFunction: dummy_func

    // a dummy function for default property values
    function dummy_func() {}

    UM.SettingPropertyProvider
    {
        id: propertyProvider
        watchedProperties: [ "value", "description" ]
    }

    UM.Label
    {
        id: fieldLabel
        anchors.left: parent.left
        anchors.verticalCenter: checkBox.verticalCenter
        visible: text != ""
        font: UM.Theme.getFont("medium")
    }

    UM.CheckBox
    {
        id: checkBox
        anchors {
            left: fieldLabel.right
            leftMargin: UM.Theme.getSize("default_margin").width
            verticalCenter: parent.verticalCenter
        }
        checked: String(propertyProvider.properties.value).toLowerCase() != 'false'
        height: UM.Theme.getSize("checkbox").height
        text: ""
        onClicked:
        {
            propertyProvider.setPropertyValue("value", checked)
            forceUpdateOnChangeFunction()
        }
    }
}
