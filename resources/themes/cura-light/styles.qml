// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.1 as UM

QtObject
{
    property Component progressbar: Component
    {
        ProgressBarStyle
        {
            background: Rectangle
            {
                implicitWidth: UM.Theme.getSize("message").width - (UM.Theme.getSize("default_margin").width * 2)
                implicitHeight: UM.Theme.getSize("progressbar").height
                color: control.hasOwnProperty("backgroundColor") ? control.backgroundColor : UM.Theme.getColor("progressbar_background")
                radius: UM.Theme.getSize("progressbar_radius").width
            }
            progress: Rectangle
            {
                color:
                {
                    if(control.indeterminate)
                    {
                        return "transparent";
                    }
                    else if(control.hasOwnProperty("controlColor"))
                    {
                        return  control.controlColor;
                    }
                    else
                    {
                        return UM.Theme.getColor("progressbar_control");
                    }
                }
                radius: UM.Theme.getSize("progressbar_radius").width
                Rectangle
                {
                    radius: UM.Theme.getSize("progressbar_radius").width
                    color: control.hasOwnProperty("controlColor") ? control.controlColor : UM.Theme.getColor("progressbar_control")
                    width: UM.Theme.getSize("progressbar_control").width
                    height: UM.Theme.getSize("progressbar_control").height
                    visible: control.indeterminate

                    SequentialAnimation on x
                    {
                        id: xAnim
                        property int animEndPoint: UM.Theme.getSize("message").width - Math.round((UM.Theme.getSize("default_margin").width * 2.5)) - UM.Theme.getSize("progressbar_control").width
                        running: control.indeterminate && control.visible
                        loops: Animation.Infinite
                        NumberAnimation { from: 0; to: xAnim.animEndPoint; duration: 2000;}
                        NumberAnimation { from: xAnim.animEndPoint; to: 0; duration: 2000;}
                    }
                }
            }
        }
    }

    property Component scrollview: Component
    {
        ScrollViewStyle
        {
            decrementControl: Item { }
            incrementControl: Item { }

            transientScrollBars: false

            scrollBarBackground: Rectangle
            {
                implicitWidth: UM.Theme.getSize("scrollbar").width
                radius: Math.round(implicitWidth / 2)
                color: UM.Theme.getColor("scrollbar_background")
            }

            handle: Rectangle
            {
                id: scrollViewHandle
                implicitWidth: UM.Theme.getSize("scrollbar").width
                radius: Math.round(implicitWidth / 2)

                color: styleData.pressed ? UM.Theme.getColor("scrollbar_handle_down") : styleData.hovered ? UM.Theme.getColor("scrollbar_handle_hover") : UM.Theme.getColor("scrollbar_handle")
                Behavior on color { ColorAnimation { duration: 50; } }
            }
        }
    }

    property Component combobox: Component
    {
        ComboBoxStyle
        {

            background: Rectangle
            {
                implicitHeight: UM.Theme.getSize("setting_control").height;
                implicitWidth: UM.Theme.getSize("setting_control").width;

                color: control.hovered ? UM.Theme.getColor("setting_control_highlight") : UM.Theme.getColor("setting_control")
                Behavior on color { ColorAnimation { duration: 50; } }

                border.width: UM.Theme.getSize("default_lining").width;
                border.color: control.hovered ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_border");
                radius: UM.Theme.getSize("setting_control_radius").width
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
                    font: UM.Theme.getFont("default");
                    color: !enabled ? UM.Theme.getColor("setting_control_disabled_text") : UM.Theme.getColor("setting_control_text")

                    elide: Text.ElideRight
                    verticalAlignment: Text.AlignVCenter
                }

                UM.RecolorImage
                {
                    id: downArrow
                    anchors.right: parent.right
                    anchors.rightMargin: UM.Theme.getSize("default_lining").width * 2
                    anchors.verticalCenter: parent.verticalCenter

                    source: UM.Theme.getIcon("ChevronSingleDown")
                    width: UM.Theme.getSize("standard_arrow").width
                    height: UM.Theme.getSize("standard_arrow").height
                    sourceSize.width: width + 5 * screenScaleFactor
                    sourceSize.height: width + 5 * screenScaleFactor

                    color: UM.Theme.getColor("setting_control_button");
                }
            }
        }
    }

    property Component partially_checkbox: Component
    {
        CheckBoxStyle
        {
            background: Item { }
            indicator: Rectangle
            {
                implicitWidth:  UM.Theme.getSize("checkbox").width
                implicitHeight: UM.Theme.getSize("checkbox").height

                color: (control.hovered || control._hovered) ? UM.Theme.getColor("checkbox_hover") : UM.Theme.getColor("checkbox");
                Behavior on color { ColorAnimation { duration: 50; } }

                radius: control.exclusiveGroup ? Math.round(UM.Theme.getSize("checkbox").width / 2) : UM.Theme.getSize("checkbox_radius").width

                border.width: UM.Theme.getSize("default_lining").width;
                border.color: (control.hovered || control._hovered) ? UM.Theme.getColor("checkbox_border_hover") : UM.Theme.getColor("checkbox_border");

                UM.RecolorImage
                {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: Math.round(parent.width / 2.5)
                    height: Math.round(parent.height / 2.5)
                    sourceSize.height: width
                    color: UM.Theme.getColor("checkbox_mark")
                    source:
                    {
                        if (control.checkbox_state == 2)
                        {
                            return UM.Theme.getIcon("Solid");
                        }
                        else
                        {
                            return control.exclusiveGroup ? UM.Theme.getIcon("Dot", "low") : UM.Theme.getIcon("Check");
                        }
                    }
                    opacity: control.checked
                    Behavior on opacity { NumberAnimation { duration: 100; } }
                }
            }
            label: Label
            {
                text: control.text
                color: UM.Theme.getColor("checkbox_text")
                font: UM.Theme.getFont("default")
            }
        }
    }
}
