// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
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

    property string tooltip: propertyProvider.properties.description ? propertyProvider.properties.description : ""

    property alias labelText: titleLabel.text
    property alias labelFont: titleLabel.font

    UM.SettingPropertyProvider
    {
        id: propertyProvider
        watchedProperties: [ "value", "description" ]
    }

    UM.Label
    {
        id: titleLabel
        anchors.top: parent.top
        anchors.left: parent.left
        font: UM.Theme.getFont("medium_bold")
    }

    Flickable
    {
        anchors
        {
            top: titleLabel.bottom
            topMargin: UM.Theme.getSize("default_margin").height
            bottom: parent.bottom
            left: parent.left
            right: parent.right
        }

        ScrollBar.vertical: UM.ScrollBar {}
        clip: true

        TextArea.flickable: TextArea
        {
            id: gcodeTextArea

            hoverEnabled: true
            selectByMouse: true

            text: (propertyProvider.properties.value) ? propertyProvider.properties.value : ""
            font: UM.Theme.getFont("fixed")
            renderType: Text.NativeRendering
            color: UM.Theme.getColor("text")
            selectionColor: UM.Theme.getColor("text_selection")
            selectedTextColor: UM.Theme.getColor("text")
            wrapMode: TextEdit.NoWrap
            padding: UM.Theme.getSize("narrow_margin").height + backgroundRectangle.border.width

            onActiveFocusChanged:
            {
                if (!activeFocus)
                {
                    propertyProvider.setPropertyValue("value", text)
                }
            }

            background: Rectangle
            {
                id: backgroundRectangle

                anchors.fill: parent

                color: UM.Theme.getColor("detail_background")
                border.color:
                {
                    if (!gcodeTextArea.enabled)
                    {
                        return UM.Theme.getColor("setting_control_disabled_border")
                    }
                    if (gcodeTextArea.hovered || gcodeTextArea.activeFocus)
                    {
                        return UM.Theme.getColor("text_field_border_active")
                    }
                    return UM.Theme.getColor("border_field_light")
                }
                border.width: UM.Theme.getSize("default_lining").width
            }
        }
    }
}
