// Copyright (c) 2016 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.1 as UM
import Cura 1.0 as Cura

SettingItem
{
    id: base

    contents: ComboBox
    {
        id: control

        model: Cura.ExtrudersModel
        {
            id: extruders_model
        }
        textRole: "name"

        anchors.fill: parent

        MouseArea
        {
            anchors.fill: parent
            acceptedButtons: Qt.NoButton
            onWheel: wheel.accepted = true;
        }

        style: ComboBoxStyle
        {
            background: Rectangle
            {
                color:
                {
                    if (!enabled)
                    {
                        return UM.Theme.getColor("setting_control_disabled");
                    }
                    if(control.hovered || base.activeFocus)
                    {
                        return UM.Theme.getColor("setting_control_highlight");
                    }
                    else
                    {
                        return extruders_model.getItem(index).colour;
                    }
                }
                border.width: UM.Theme.getSize("default_lining").width
                border.color: !enabled ? UM.Theme.getColor("setting_control_disabled_border") : control.hovered ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_border")
            }
            label: Item
            {
                Label
                {
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_lining").width
                    anchors.right: downArrow.left
                    anchors.rightMargin: UM.Theme.getSize("default_lining").width
                    anchors.verticalCenter: parent.verticalCenter

                    text: control.currentText
                    font: UM.Theme.getFont("default")
                    color: !enabled ? UM.Theme.getColor("setting_control_disabled_text") : extruders_model.getItem(index).colour

                    elide: Text.ElideRight
                    verticalAlignment: Text.AlignVCenter
                }

                UM.RecolorImage
                {
                    id: downArrow
                    anchors.right: parent.right
                    anchors.rightMargin: UM.Theme.getSize("default_lining").width * 2
                    anchors.verticalCenter: parent.verticalCenter

                    source: UM.Theme.getIcon("arrow_bottom")
                    width: UM.Theme.getSize("standard_arrow").width
                    height: UM.Theme.getSize("standard_arrow").height
                    sourceSize.width: width + 5
                    sourceSize.height: width + 5

                    color: UM.Theme.getColor("setting_control_text")
                }
            }
        }

        onActivated: provider.setPropertyValue("value", extruders_model.getItem(index).index);
        onModelChanged: updateCurrentIndex();

        Connections
        {
            target: provider
            onPropertiesChanged: control.updateCurrentIndex();
        }

        function updateCurrentIndex()
        {
            for(var i = 0; i < extruders_model.rowCount(); ++i)
            {
                if(extruders_model.getItem(i).index == provider.properties.value)
                {
                    currentIndex = i;
                    return;
                }
            }
            currentIndex = -1;
        }
    }
}
