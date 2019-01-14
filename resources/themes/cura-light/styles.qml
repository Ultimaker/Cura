// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.1 as UM

QtObject
{
    property Component print_setup_header_button: Component
    {
        ButtonStyle
        {
            background: Rectangle
            {
                color:
                {
                    if(control.enabled)
                    {
                        if(control.valueError)
                        {
                            return Theme.getColor("setting_validation_error_background");
                        }
                        else if(control.valueWarning)
                        {
                            return Theme.getColor("setting_validation_warning_background");
                        }
                        else
                        {
                            return Theme.getColor("setting_control");
                        }
                    }
                    else
                    {
                        return Theme.getColor("setting_control_disabled");
                    }
                }

                radius: UM.Theme.getSize("setting_control_radius").width
                border.width: Theme.getSize("default_lining").width
                border.color:
                {
                    if (control.enabled)
                    {
                        if (control.valueError)
                        {
                            return Theme.getColor("setting_validation_error");
                        }
                        else if (control.valueWarning)
                        {
                            return Theme.getColor("setting_validation_warning");
                        }
                        else if (control.hovered)
                        {
                            return Theme.getColor("setting_control_border_highlight");
                        }
                        else
                        {
                            return Theme.getColor("setting_control_border");
                        }
                    }
                    else
                    {
                        return Theme.getColor("setting_control_disabled_border");
                    }
                }
                UM.RecolorImage
                {
                    id: downArrow
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    anchors.rightMargin: Theme.getSize("default_margin").width
                    width: Theme.getSize("standard_arrow").width
                    height: Theme.getSize("standard_arrow").height
                    sourceSize.height: width
                    color: control.enabled ? Theme.getColor("setting_control_button") : Theme.getColor("setting_category_disabled_text")
                    source: Theme.getIcon("arrow_bottom")
                }
                Label
                {
                    id: printSetupComboBoxLabel
                    color: control.enabled ? Theme.getColor("setting_control_text") : Theme.getColor("setting_control_disabled_text")
                    text: control.text;
                    elide: Text.ElideRight;
                    anchors.left: parent.left;
                    anchors.leftMargin: Theme.getSize("setting_unit_margin").width
                    anchors.right: downArrow.left;
                    anchors.rightMargin: control.rightMargin;
                    anchors.verticalCenter: parent.verticalCenter;
                    font: Theme.getFont("default")
                }
            }
            label: Label{}
        }
    }

    property Component main_window_header_tab: Component
    {
        ButtonStyle
        {
            // This property will be back-propagated when the width of the label is calculated
            property var buttonWidth: 0

            background: Item
            {
                implicitHeight: control.height
                implicitWidth: buttonWidth
                Rectangle
                {
                    id: buttonFace
                    implicitHeight: parent.height
                    implicitWidth: parent.width
                    radius: UM.Theme.getSize("action_button_radius").width

                    color:
                    {
                        if (control.checked)
                        {
                            return UM.Theme.getColor("main_window_header_button_background_active")
                        }
                        else
                        {
                            if (control.hovered)
                            {
                                return UM.Theme.getColor("main_window_header_button_background_hovered")
                            }
                            return UM.Theme.getColor("main_window_header_button_background_inactive")
                        }
                    }
                }
            }

            label: Item
            {
                id: contents
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.verticalCenter: parent.verticalCenter
                height: control.height
                width: buttonLabel.width + 4 * UM.Theme.getSize("default_margin").width

                Label
                {
                    id: buttonLabel
                    text: control.text
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    font: UM.Theme.getFont("medium")
                    color:
                    {
                        if (control.checked)
                        {
                            return UM.Theme.getColor("main_window_header_button_text_active")
                        }
                        else
                        {
                            if (control.hovered)
                            {
                                return UM.Theme.getColor("main_window_header_button_text_hovered")
                            }
                            return UM.Theme.getColor("main_window_header_button_text_inactive")
                        }
                    }
                }
                Component.onCompleted:
                {
                    buttonWidth = width
                }
            }
        }
    }

    property Component tool_button: Component
    {
        ButtonStyle
        {
            background: Item
            {
                implicitWidth: Theme.getSize("button").width
                implicitHeight: Theme.getSize("button").height

                UM.PointingRectangle
                {
                    id: button_tooltip

                    anchors.left: parent.right
                    anchors.leftMargin: Theme.getSize("button_tooltip_arrow").width * 2
                    anchors.verticalCenter: parent.verticalCenter

                    target: Qt.point(parent.x, y + Math.round(height/2))
                    arrowSize: Theme.getSize("button_tooltip_arrow").width
                    color: Theme.getColor("button_tooltip")
                    opacity: control.hovered ? 1.0 : 0.0;
                    visible: control.text != ""

                    width: control.hovered ? button_tip.width + Theme.getSize("button_tooltip").width : 0
                    height: Theme.getSize("button_tooltip").height

                    Behavior on width { NumberAnimation { duration: 100; } }
                    Behavior on opacity { NumberAnimation { duration: 100; } }

                    Label
                    {
                        id: button_tip

                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.verticalCenter: parent.verticalCenter

                        text: control.text
                        font: Theme.getFont("default")
                        color: Theme.getColor("tooltip_text")
                    }
                }

                Rectangle
                {
                    id: buttonFace

                    anchors.fill: parent
                    property bool down: control.pressed || (control.checkable && control.checked)

                    color:
                    {
                        if(control.customColor !== undefined && control.customColor !== null)
                        {
                            return control.customColor
                        }
                        else if(control.checkable && control.checked && control.hovered)
                        {
                            return Theme.getColor("toolbar_button_active_hover")
                        }
                        else if(control.pressed || (control.checkable && control.checked))
                        {
                            return Theme.getColor("toolbar_button_active")
                        }
                        else if(control.hovered)
                        {
                            return Theme.getColor("toolbar_button_hover")
                        }
                        return Theme.getColor("toolbar_background")
                    }
                    Behavior on color { ColorAnimation { duration: 50; } }

                    border.width: (control.hasOwnProperty("needBorder") && control.needBorder) ? Theme.getSize("default_lining").width : 0
                    border.color: Theme.getColor("lining")
                }
            }

            label: Item
            {
                UM.RecolorImage
                {
                    anchors.centerIn: parent
                    opacity: control.enabled ? 1.0 : 0.2
                    source: control.iconSource
                    width: Theme.getSize("button_icon").width
                    height: Theme.getSize("button_icon").height
                    color: Theme.getColor("icon")

                    sourceSize: Theme.getSize("button_icon")
                }
            }
        }
    }

    property Component progressbar: Component
    {
        ProgressBarStyle
        {
            background: Rectangle
            {
                implicitWidth: Theme.getSize("message").width - (Theme.getSize("default_margin").width * 2)
                implicitHeight: Theme.getSize("progressbar").height
                color: control.hasOwnProperty("backgroundColor") ? control.backgroundColor : Theme.getColor("progressbar_background")
                radius: Theme.getSize("progressbar_radius").width
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
                        return Theme.getColor("progressbar_control");
                    }
                }
                radius: Theme.getSize("progressbar_radius").width
                Rectangle
                {
                    radius: Theme.getSize("progressbar_radius").width
                    color: control.hasOwnProperty("controlColor") ? control.controlColor : Theme.getColor("progressbar_control")
                    width: Theme.getSize("progressbar_control").width
                    height: Theme.getSize("progressbar_control").height
                    visible: control.indeterminate

                    SequentialAnimation on x
                    {
                        id: xAnim
                        property int animEndPoint: Theme.getSize("message").width - Math.round((Theme.getSize("default_margin").width * 2.5)) - Theme.getSize("progressbar_control").width
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
                implicitWidth: Theme.getSize("scrollbar").width
                radius: Math.round(implicitWidth / 2)
                color: Theme.getColor("scrollbar_background")
            }

            handle: Rectangle
            {
                id: scrollViewHandle
                implicitWidth: Theme.getSize("scrollbar").width
                radius: Math.round(implicitWidth / 2)

                color: styleData.pressed ? Theme.getColor("scrollbar_handle_down") : styleData.hovered ? Theme.getColor("scrollbar_handle_hover") : Theme.getColor("scrollbar_handle")
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
                implicitHeight: Theme.getSize("setting_control").height;
                implicitWidth: Theme.getSize("setting_control").width;

                color: control.hovered ? UM.Theme.getColor("setting_control_highlight") : UM.Theme.getColor("setting_control")
                Behavior on color { ColorAnimation { duration: 50; } }

                border.width: Theme.getSize("default_lining").width;
                border.color: control.hovered ? Theme.getColor("setting_control_border_highlight") : Theme.getColor("setting_control_border");
                radius: UM.Theme.getSize("setting_control_radius").width
            }

            label: Item
            {
                Label
                {
                    anchors.left: parent.left
                    anchors.leftMargin: Theme.getSize("default_lining").width
                    anchors.right: downArrow.left
                    anchors.rightMargin: Theme.getSize("default_lining").width
                    anchors.verticalCenter: parent.verticalCenter

                    text: control.currentText
                    font: Theme.getFont("default");
                    color: !enabled ? Theme.getColor("setting_control_disabled_text") : Theme.getColor("setting_control_text")

                    elide: Text.ElideRight
                    verticalAlignment: Text.AlignVCenter
                }

                UM.RecolorImage
                {
                    id: downArrow
                    anchors.right: parent.right
                    anchors.rightMargin: Theme.getSize("default_lining").width * 2
                    anchors.verticalCenter: parent.verticalCenter

                    source: Theme.getIcon("arrow_bottom")
                    width: Theme.getSize("standard_arrow").width
                    height: Theme.getSize("standard_arrow").height
                    sourceSize.width: width + 5 * screenScaleFactor
                    sourceSize.height: width + 5 * screenScaleFactor

                    color: Theme.getColor("setting_control_button");
                }
            }
        }
    }

    // Combobox with items with colored rectangles
    property Component combobox_color: Component
    {

        ComboBoxStyle
        {

            background: Rectangle
            {
                color: !enabled ? UM.Theme.getColor("setting_control_disabled") : control._hovered ? UM.Theme.getColor("setting_control_highlight") : UM.Theme.getColor("setting_control")
                border.width: UM.Theme.getSize("default_lining").width
                border.color: !enabled ? UM.Theme.getColor("setting_control_disabled_border") : control._hovered ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_border")
                radius: UM.Theme.getSize("setting_control_radius").width
            }

            label: Item
            {
                Label
                {
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_lining").width
                    anchors.right: swatch.left
                    anchors.rightMargin: UM.Theme.getSize("default_lining").width
                    anchors.verticalCenter: parent.verticalCenter

                    text: control.currentText
                    font: UM.Theme.getFont("default")
                    color: !enabled ? UM.Theme.getColor("setting_control_disabled_text") : UM.Theme.getColor("setting_control_text")

                    elide: Text.ElideRight
                    verticalAlignment: Text.AlignVCenter
                }

                UM.RecolorImage
                {
                    id: swatch
                    height: Math.round(control.height / 2)
                    width: height
                    anchors.right: downArrow.left
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.rightMargin: UM.Theme.getSize("default_margin").width

                    sourceSize.width: width
                    sourceSize.height: height
                    source: UM.Theme.getIcon("extruder_button")
                    color: (control.color_override !== "") ? control.color_override : control.color
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
                    sourceSize.width: width + 5 * screenScaleFactor
                    sourceSize.height: width + 5 * screenScaleFactor

                    color: UM.Theme.getColor("setting_control_button")
                }
            }
        }
    }

    property Component checkbox: Component
    {
        CheckBoxStyle
        {
            background: Item { }
            indicator: Rectangle
            {
                implicitWidth:  Theme.getSize("checkbox").width
                implicitHeight: Theme.getSize("checkbox").height

                color: (control.hovered || control._hovered) ? Theme.getColor("checkbox_hover") : (control.enabled ? Theme.getColor("checkbox") : Theme.getColor("checkbox_disabled"))
                Behavior on color { ColorAnimation { duration: 50; } }

                radius: control.exclusiveGroup ? Math.round(Theme.getSize("checkbox").width / 2) : Theme.getSize("checkbox_radius").width

                border.width: Theme.getSize("default_lining").width
                border.color: (control.hovered || control._hovered) ? Theme.getColor("checkbox_border_hover") : Theme.getColor("checkbox_border")

                UM.RecolorImage
                {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: Math.round(parent.width / 2.5)
                    height: Math.round(parent.height / 2.5)
                    sourceSize.height: width
                    color: Theme.getColor("checkbox_mark")
                    source: control.exclusiveGroup ? Theme.getIcon("dot") : Theme.getIcon("check")
                    opacity: control.checked
                    Behavior on opacity { NumberAnimation { duration: 100; } }
                }
            }
            label: Label
            {
                text: control.text
                color: Theme.getColor("checkbox_text")
                font: Theme.getFont("default")
                elide: Text.ElideRight
                renderType: Text.NativeRendering
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
                implicitWidth:  Theme.getSize("checkbox").width
                implicitHeight: Theme.getSize("checkbox").height

                color: (control.hovered || control._hovered) ? Theme.getColor("checkbox_hover") : Theme.getColor("checkbox");
                Behavior on color { ColorAnimation { duration: 50; } }

                radius: control.exclusiveGroup ? Math.round(Theme.getSize("checkbox").width / 2) : UM.Theme.getSize("checkbox_radius").width

                border.width: Theme.getSize("default_lining").width;
                border.color: (control.hovered || control._hovered) ? Theme.getColor("checkbox_border_hover") : Theme.getColor("checkbox_border");

                UM.RecolorImage
                {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: Math.round(parent.width / 2.5)
                    height: Math.round(parent.height / 2.5)
                    sourceSize.height: width
                    color: Theme.getColor("checkbox_mark")
                    source:
                    {
                        if (control.checkbox_state == 2)
                        {
                            return Theme.getIcon("solid");
                        }
                        else
                        {
                            return control.exclusiveGroup ? Theme.getIcon("dot") : Theme.getIcon("check");
                        }
                    }
                    opacity: control.checked
                    Behavior on opacity { NumberAnimation { duration: 100; } }
                }
            }
            label: Label
            {
                text: control.text
                color: Theme.getColor("checkbox_text")
                font: Theme.getFont("default")
            }
        }
    }

    property Component text_field: Component
    {
        TextFieldStyle
        {
            textColor: Theme.getColor("setting_control_text")
            placeholderTextColor: Theme.getColor("setting_control_text")
            font: Theme.getFont("default")

            background: Rectangle
            {
                implicitHeight: control.height;
                implicitWidth: control.width;

                border.width: Theme.getSize("default_lining").width;
                border.color: control.hovered ? Theme.getColor("setting_control_border_highlight") : Theme.getColor("setting_control_border");
                radius: UM.Theme.getSize("setting_control_radius").width

                color: Theme.getColor("setting_validation_ok");

                Label
                {
                    anchors.right: parent.right;
                    anchors.rightMargin: Theme.getSize("setting_unit_margin").width;
                    anchors.verticalCenter: parent.verticalCenter;

                    text: control.unit ? control.unit : ""
                    color: Theme.getColor("setting_unit");
                    font: Theme.getFont("default");
                    renderType: Text.NativeRendering
                }
            }
        }
    }

    property Component print_setup_action_button: Component
    {
        ButtonStyle
        {
            background: Rectangle
            {
                border.width: UM.Theme.getSize("default_lining").width
                border.color:
                {
                    if(!control.enabled)
                    {
                        return UM.Theme.getColor("action_button_disabled_border");
                    }
                    else if(control.pressed)
                    {
                        return UM.Theme.getColor("action_button_active_border");
                    }
                    else if(control.hovered)
                    {
                        return UM.Theme.getColor("action_button_hovered_border");
                    }
                    else
                    {
                        return UM.Theme.getColor("action_button_border");
                    }
                }
                color:
                {
                    if(!control.enabled)
                    {
                        return UM.Theme.getColor("action_button_disabled");
                    }
                    else if(control.pressed)
                    {
                        return UM.Theme.getColor("action_button_active");
                    }
                    else if(control.hovered)
                    {
                        return UM.Theme.getColor("action_button_hovered");
                    }
                    else
                    {
                        return UM.Theme.getColor("action_button");
                    }
                }
                Behavior on color { ColorAnimation { duration: 50 } }

                implicitWidth: actualLabel.contentWidth + (UM.Theme.getSize("thick_margin").width * 2)

                Label
                {
                    id: actualLabel
                    anchors.centerIn: parent
                    color:
                    {
                        if(!control.enabled)
                        {
                            return UM.Theme.getColor("action_button_disabled_text");
                        }
                        else if(control.pressed)
                        {
                            return UM.Theme.getColor("action_button_active_text");
                        }
                        else if(control.hovered)
                        {
                            return UM.Theme.getColor("action_button_hovered_text");
                        }
                        else
                        {
                            return UM.Theme.getColor("action_button_text");
                        }
                    }
                    font: UM.Theme.getFont("medium")
                    text: control.text
                }
            }
            label: Item { }
        }
    }

    property Component toolbox_action_button: Component
    {
        ButtonStyle
        {
            background: Rectangle
            {
                implicitWidth: UM.Theme.getSize("toolbox_action_button").width
                implicitHeight: UM.Theme.getSize("toolbox_action_button").height
                color:
                {
                    if (control.installed)
                    {
                        return UM.Theme.getColor("action_button_disabled");
                    }
                    else
                    {
                        if (control.hovered)
                        {
                            return UM.Theme.getColor("primary_hover");
                        }
                        else
                        {
                            return UM.Theme.getColor("primary");
                        }
                    }

                }
            }
            label: Label
            {
                text: control.text
                color:
                {
                    if (control.installed)
                    {
                        return UM.Theme.getColor("action_button_disabled_text");
                    }
                    else
                    {
                        if (control.hovered)
                        {
                            return UM.Theme.getColor("button_text_hover");
                        }
                        else
                        {
                            return UM.Theme.getColor("button_text");
                        }
                    }
                }
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font: UM.Theme.getFont("default_bold")
            }
        }
    }

    property Component monitor_button_style: Component
    {
        ButtonStyle
        {
            background: Rectangle
            {
                border.width: UM.Theme.getSize("default_lining").width
                border.color:
                {
                    if(!control.enabled)
                    {
                        return UM.Theme.getColor("action_button_disabled_border");
                    }
                    else if(control.pressed)
                    {
                        return UM.Theme.getColor("action_button_active_border");
                    }
                    else if(control.hovered)
                    {
                        return UM.Theme.getColor("action_button_hovered_border");
                    }
                    return UM.Theme.getColor("action_button_border");
                }
                color:
                {
                    if(!control.enabled)
                    {
                        return UM.Theme.getColor("action_button_disabled");
                    }
                    else if(control.pressed)
                    {
                        return UM.Theme.getColor("action_button_active");
                    }
                    else if(control.hovered)
                    {
                        return UM.Theme.getColor("action_button_hovered");
                    }
                    return UM.Theme.getColor("action_button");
                }
                Behavior on color
                {
                    ColorAnimation
                    {
                        duration: 50
                    }
                }
            }

            label: Item
            {
                UM.RecolorImage
                {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: Math.floor(control.width / 2)
                    height: Math.floor(control.height / 2)
                    sourceSize.height: width
                    color:
                    {
                        if(!control.enabled)
                        {
                            return UM.Theme.getColor("action_button_disabled_text");
                        }
                        else if(control.pressed)
                        {
                            return UM.Theme.getColor("action_button_active_text");
                        }
                        else if(control.hovered)
                        {
                            return UM.Theme.getColor("action_button_hovered_text");
                        }
                        return UM.Theme.getColor("action_button_text");
                    }
                    source: control.iconSource
                }
            }
        }
    }

    property Component monitor_checkable_button_style: Component
    {
        ButtonStyle {
            background: Rectangle {
                border.width: control.checked ? UM.Theme.getSize("default_lining").width * 2 : UM.Theme.getSize("default_lining").width
                border.color:
                {
                    if(!control.enabled)
                    {
                        return UM.Theme.getColor("action_button_disabled_border");
                    }
                    else if (control.checked || control.pressed)
                    {
                        return UM.Theme.getColor("action_button_active_border");
                    }
                    else if(control.hovered)
                    {
                        return UM.Theme.getColor("action_button_hovered_border");
                    }
                    return UM.Theme.getColor("action_button_border");
                }
                color:
                {
                    if(!control.enabled)
                    {
                        return UM.Theme.getColor("action_button_disabled");
                    }
                    else if (control.checked || control.pressed)
                    {
                        return UM.Theme.getColor("action_button_active");
                    }
                    else if (control.hovered)
                    {
                        return UM.Theme.getColor("action_button_hovered");
                    }
                    return UM.Theme.getColor("action_button");
                }
                Behavior on color { ColorAnimation { duration: 50; } }
                Label {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: UM.Theme.getSize("default_lining").width * 2
                    anchors.rightMargin: UM.Theme.getSize("default_lining").width * 2
                    color:
                    {
                        if(!control.enabled)
                        {
                            return UM.Theme.getColor("action_button_disabled_text");
                        }
                        else if (control.checked || control.pressed)
                        {
                            return UM.Theme.getColor("action_button_active_text");
                        }
                        else if (control.hovered)
                        {
                            return UM.Theme.getColor("action_button_hovered_text");
                        }
                        return UM.Theme.getColor("action_button_text");
                    }
                    font: UM.Theme.getFont("default")
                    text: control.text
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideMiddle
                }
            }
            label: Item { }
        }
    }
}
