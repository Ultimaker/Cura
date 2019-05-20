// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// TextArea widget for editing Gcode in the Machine Settings dialog.
//
UM.TooltipArea
{
    id: control

    UM.I18nCatalog { id: catalog; name: "cura"; }

    text: tooltip

    property alias containerStackId: propertyProvider.containerStackId
    property alias settingKey: propertyProvider.key
    property alias settingStoreIndex: propertyProvider.storeIndex

    property string tooltip: propertyProvider.properties.description

    property alias labelText: titleLabel.text
    property alias labelFont: titleLabel.font

    UM.SettingPropertyProvider
    {
        id: propertyProvider
        watchedProperties: [ "value", "description" ]
    }

    Label   // Title Label
    {
        id: titleLabel
        anchors.top: parent.top
        anchors.left: parent.left
        font: UM.Theme.getFont("medium_bold")
        color: UM.Theme.getColor("text")
        renderType: Text.NativeRendering
    }

    ScrollView
    {
        anchors.top: titleLabel.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right

        background: Rectangle
        {
            color: UM.Theme.getColor("main_background")
            anchors.fill: parent

            border.color:
            {
                if (!gcodeTextArea.enabled)
                {
                    return UM.Theme.getColor("setting_control_disabled_border")
                }
                if (gcodeTextArea.hovered || gcodeTextArea.activeFocus)
                {
                    return UM.Theme.getColor("setting_control_border_highlight")
                }
                return UM.Theme.getColor("setting_control_border")
            }
        }

        TextArea
        {
            id: gcodeTextArea

            hoverEnabled: true
            selectByMouse: true

            text: (propertyProvider.properties.value) ? propertyProvider.properties.value : ""
            font: UM.Theme.getFont("fixed")
            renderType: Text.NativeRendering
            color: UM.Theme.getColor("text")
            wrapMode: TextEdit.NoWrap

            onActiveFocusChanged:
            {
                if (!activeFocus)
                {
                    propertyProvider.setPropertyValue("value", text)
                }
            }
        }
    }
}
