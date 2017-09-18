// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.1 as UM

QtObject {
    property Component sidebar_header_button: Component {
        ButtonStyle {
            background: Rectangle {
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
                UM.RecolorImage {
                    id: downArrow
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    anchors.rightMargin: Theme.getSize("default_margin").width
                    width: Theme.getSize("standard_arrow").width
                    height: Theme.getSize("standard_arrow").height
                    sourceSize.width: width
                    sourceSize.height: width
                    color: control.enabled ? Theme.getColor("setting_category_text") : Theme.getColor("setting_category_disabled_text")
                    source: Theme.getIcon("arrow_bottom")
                }
                Label {
                    id: sidebarComboBoxLabel
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

    property Component topbar_header_tab_no_overlay: Component {
        ButtonStyle {
            background: Rectangle {
                implicitHeight: Theme.getSize("topbar_button").height
                implicitWidth: Theme.getSize("topbar_button").width
                color: "transparent"
                anchors.fill: parent

                Rectangle
                {
                    id: underline

                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    width: parent.width
                    height: Theme.getSize("sidebar_header_highlight").height
                    color: control.checked ? UM.Theme.getColor("sidebar_header_highlight") : UM.Theme.getColor("sidebar_header_highlight_hover")
                    visible: control.hovered || control.checked
                }
            }

            label: Rectangle {
                implicitHeight: Theme.getSize("topbar_button_icon").height
                implicitWidth: Theme.getSize("topbar_button").width
                color: "transparent"
                anchors.fill: parent

                Item
                {
                    anchors.centerIn: parent
                    width: textLabel.width + icon.width + Theme.getSize("default_margin").width / 2
                    Label
                    {
                        id: textLabel
                        text: control.text
                        anchors.right: icon.visible ? icon.left : parent.right
                        anchors.rightMargin: icon.visible ? Theme.getSize("default_margin").width / 2 : 0
                        anchors.verticalCenter: parent.verticalCenter;
                        font: control.checked ? UM.Theme.getFont("large") : UM.Theme.getFont("large_nonbold")
                        color:
                        {
                            if(control.hovered)
                            {
                                return UM.Theme.getColor("topbar_button_text_hovered");
                            }
                            if(control.checked)
                            {
                                return UM.Theme.getColor("topbar_button_text_active");
                            }
                            else
                            {
                                return UM.Theme.getColor("topbar_button_text_inactive");
                            }
                        }
                    }
                    Image
                    {
                        id: icon
                        visible: control.iconSource != ""
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        opacity: !control.enabled ? 0.2 : 1.0
                        source: control.iconSource
                        width: visible ? Theme.getSize("topbar_button_icon").width : 0
                        height: Theme.getSize("topbar_button_icon").height

                        sourceSize: Theme.getSize("topbar_button_icon")
                    }
                }
            }
        }
    }

    property Component topbar_header_tab: Component {
        ButtonStyle {
            background: Item {
                implicitHeight: Theme.getSize("topbar_button").height
                implicitWidth: Theme.getSize("topbar_button").width + Theme.getSize("topbar_button_icon").width

                Rectangle {
                    id: buttonFace;
                    anchors.fill: parent;

                    color: "transparent"
                    Behavior on color { ColorAnimation { duration: 50; } }

                    Rectangle {
                        id: underline;

                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.bottom: parent.bottom
                        width: Theme.getSize("topbar_button").width + Theme.getSize("topbar_button_icon").width
                        height: Theme.getSize("sidebar_header_highlight").height
                        color: control.checked ? UM.Theme.getColor("sidebar_header_highlight") : UM.Theme.getColor("sidebar_header_highlight_hover")
                        visible: control.hovered || control.checked
                    }
                }
            }

            label: Item
            {
                implicitHeight: Theme.getSize("topbar_button_icon").height
                implicitWidth: Theme.getSize("topbar_button").width + Theme.getSize("topbar_button_icon").width
                Item
                {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.verticalCenter: parent.verticalCenter;
                    width: childrenRect.width
                    height: Theme.getSize("topbar_button_icon").height
                    Label
                    {
                        text: control.text;
                        anchors.right: (icon.visible || overlayIcon.visible) ? icon.left : parent.right
                        anchors.rightMargin: (icon.visible || overlayIcon.visible) ? Theme.getSize("default_margin").width : 0
                        anchors.verticalCenter: parent.verticalCenter;
                        font: control.checked ? UM.Theme.getFont("large") : UM.Theme.getFont("large_nonbold")
                        color:
                        {
                            if(control.hovered)
                            {
                                return UM.Theme.getColor("topbar_button_text_hovered");
                            }
                            if(control.checked)
                            {
                                return UM.Theme.getColor("topbar_button_text_active");
                            }
                            else
                            {
                                return UM.Theme.getColor("topbar_button_text_inactive");
                            }
                        }
                    }
                    UM.RecolorImage
                    {
                        visible: control.iconSource != ""
                        id: icon
                        color: UM.Theme.getColor("text_emphasis")
                        opacity: !control.enabled ? 0.2 : 1.0
                        source: control.iconSource
                        width: visible ? Theme.getSize("topbar_button_icon").width : 0
                        height: Theme.getSize("topbar_button_icon").height

                        sourceSize: Theme.getSize("topbar_button_icon")
                    }
                    UM.RecolorImage
                    {
                        id: overlayIcon
                        visible: control.overlayIconSource != "" && control.iconSource != ""
                        color: control.overlayColor
                        opacity: !control.enabled ? 0.2 : 1.0
                        source: control.overlayIconSource
                        width: visible ? Theme.getSize("topbar_button_icon").width : 0
                        height: Theme.getSize("topbar_button_icon").height

                        sourceSize: Theme.getSize("topbar_button_icon")
                    }
                }
            }
        }
    }

    property Component tool_button: Component {
        ButtonStyle {
            background: Item {
                implicitWidth: Theme.getSize("button").width;
                implicitHeight: Theme.getSize("button").height;

                UM.PointingRectangle {
                    id: button_tooltip

                    anchors.left: parent.right
                    anchors.leftMargin: Theme.getSize("button_tooltip_arrow").width * 2
                    anchors.verticalCenter: parent.verticalCenter

                    target: Qt.point(parent.x, y + height/2)
                    arrowSize: Theme.getSize("button_tooltip_arrow").width
                    color: Theme.getColor("button_tooltip")
                    opacity: control.hovered ? 1.0 : 0.0;

                    width: control.hovered ? button_tip.width + Theme.getSize("button_tooltip").width : 0
                    height: Theme.getSize("button_tooltip").height

                    Behavior on width { NumberAnimation { duration: 100; } }
                    Behavior on opacity { NumberAnimation { duration: 100; } }

                    Label {
                        id: button_tip

                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.verticalCenter: parent.verticalCenter;

                        text: control.text;
                        font: Theme.getFont("button_tooltip");
                        color: Theme.getColor("tooltip_text");
                    }
                }

                Rectangle {
                    id: buttonFace;

                    anchors.fill: parent;
                    property bool down: control.pressed || (control.checkable && control.checked);

                    color: {
                        if(control.customColor !== undefined && control.customColor !== null) {
                            return control.customColor
                        } else if(control.checkable && control.checked && control.hovered) {
                            return Theme.getColor("button_active_hover");
                        } else if(control.pressed || (control.checkable && control.checked)) {
                            return Theme.getColor("button_active");
                        } else if(control.hovered) {
                            return Theme.getColor("button_hover");
                        } else {
                            return Theme.getColor("button");
                        }
                    }
                    Behavior on color { ColorAnimation { duration: 50; } }

                    border.width: (control.hasOwnProperty("needBorder") && control.needBorder) ? 2 : 0
                    border.color: Theme.getColor("tool_button_border")

                    UM.RecolorImage {
                        id: tool_button_arrow
                        anchors.right: parent.right;
                        anchors.rightMargin: (Theme.getSize("button").width - Theme.getSize("button_icon").width) / 4
                        anchors.bottom: parent.bottom;
                        anchors.bottomMargin: (Theme.getSize("button").height - Theme.getSize("button_icon").height) / 4
                        width: Theme.getSize("standard_arrow").width
                        height: Theme.getSize("standard_arrow").height
                        sourceSize.width: width
                        sourceSize.height: width
                        visible: control.menu != null;
                        color:
                        {
                            if(control.checkable && control.checked && control.hovered)
                            {
                                return Theme.getColor("button_text_active_hover");
                            }
                            else if(control.pressed || (control.checkable && control.checked))
                            {
                                return Theme.getColor("button_text_active");
                            }
                            else if(control.hovered)
                            {
                                return Theme.getColor("button_text_hover");
                            }
                            else
                            {
                                return Theme.getColor("button_text");
                            }
                        }
                        source: Theme.getIcon("arrow_bottom")
                    }
                }
            }

            label: Item {
                UM.RecolorImage {
                    anchors.centerIn: parent;
                    opacity: !control.enabled ? 0.2 : 1.0
                    source: control.iconSource;
                    width: Theme.getSize("button_icon").width;
                    height: Theme.getSize("button_icon").height;
                    color:
                    {
                        if(control.checkable && control.checked && control.hovered)
                        {
                            return Theme.getColor("button_text_active_hover");
                        }
                        else if(control.pressed || (control.checkable && control.checked))
                        {
                            return Theme.getColor("button_text_active");
                        }
                        else if(control.hovered)
                        {
                            return Theme.getColor("button_text_hover");
                        }
                        else
                        {
                            return Theme.getColor("button_text");
                        }
                    }

                    sourceSize: Theme.getSize("button_icon")
                }
            }
        }
    }

    property Component progressbar: Component{
        ProgressBarStyle {
            background: Rectangle {
                implicitWidth: Theme.getSize("message").width - (Theme.getSize("default_margin").width * 2)
                implicitHeight: Theme.getSize("progressbar").height
                color: control.hasOwnProperty("backgroundColor") ? control.backgroundColor : Theme.getColor("progressbar_background")
            }
            progress: Rectangle {
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
                Rectangle{
                    radius: Theme.getSize("progressbar_radius").width
                    color: control.hasOwnProperty("controlColor") ? control.controlColor : Theme.getColor("progressbar_control")
                    width: Theme.getSize("progressbar_control").width
                    height: Theme.getSize("progressbar_control").height
                    visible: control.indeterminate

                    SequentialAnimation on x {
                        id: xAnim
                        property int animEndPoint: Theme.getSize("message").width - (Theme.getSize("default_margin").width * 2) - Theme.getSize("progressbar_control").width
                        running: control.indeterminate && control.visible
                        loops: Animation.Infinite
                        NumberAnimation { from: 0; to: xAnim.animEndPoint; duration: 2000;}
                        NumberAnimation { from: xAnim.animEndPoint; to: 0; duration: 2000;}
                    }
                }
            }
        }
    }

    property Component sidebar_category: Component {
        ButtonStyle {
            background: Rectangle {
                anchors.fill: parent;
                anchors.left: parent.left
                anchors.leftMargin: Theme.getSize("sidebar_margin").width
                anchors.right: parent.right
                anchors.rightMargin: Theme.getSize("sidebar_margin").width
                implicitHeight: Theme.getSize("section").height;
                color: {
                    if(control.color) {
                        return control.color;
                    } else if(!control.enabled) {
                        return Theme.getColor("setting_category_disabled");
                    } else if(control.hovered && control.checkable && control.checked) {
                        return Theme.getColor("setting_category_active_hover");
                    } else if(control.pressed || (control.checkable && control.checked)) {
                        return Theme.getColor("setting_category_active");
                    } else if(control.hovered) {
                        return Theme.getColor("setting_category_hover");
                    } else {
                        return Theme.getColor("setting_category");
                    }
                }
                Behavior on color { ColorAnimation { duration: 50; } }
                Rectangle {
                    height: Theme.getSize("default_lining").height
                    width: parent.width
                    anchors.bottom: parent.bottom
                    color: {
                        if(!control.enabled) {
                            return Theme.getColor("setting_category_disabled_border");
                        } else if((control.hovered || control.activeFocus) && control.checkable && control.checked) {
                            return Theme.getColor("setting_category_active_hover_border");
                        } else if(control.pressed || (control.checkable && control.checked)) {
                            return Theme.getColor("setting_category_active_border");
                        } else if(control.hovered || control.activeFocus) {
                            return Theme.getColor("setting_category_hover_border");
                        } else {
                            return Theme.getColor("setting_category_border");
                        }
                    }
                }
            }
            label: Item {
                anchors.fill: parent;
                anchors.left: parent.left
                Item{
                    id: icon;
                    anchors.left: parent.left
                    height: parent.height
                    width: Theme.getSize("section_icon_column").width
                    UM.RecolorImage {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: Theme.getSize("sidebar_margin").width
                        color:
                        {
                            if(!control.enabled)
                            {
                                return Theme.getColor("setting_category_disabled_text");
                            }
                            else if((control.hovered || control.activeFocus) && control.checkable && control.checked)
                            {
                                return Theme.getColor("setting_category_active_hover_text");
                            }
                            else if(control.pressed || (control.checkable && control.checked))
                            {
                                return Theme.getColor("setting_category_active_text");
                            }
                            else if(control.hovered || control.activeFocus)
                            {
                                return Theme.getColor("setting_category_hover_text");
                            }
                            else
                            {
                                return Theme.getColor("setting_category_text");
                            }
                        }
                        source: control.iconSource;
                        width: Theme.getSize("section_icon").width;
                        height: Theme.getSize("section_icon").height;
                        sourceSize.width: width + 15
                        sourceSize.height: width + 15
                    }
                }

                Label {
                    anchors {
                        left: icon.right;
                        leftMargin: Theme.getSize("default_margin").width;
                        right: parent.right;
                        verticalCenter: parent.verticalCenter;
                    }
                    text: control.text;
                    font: Theme.getFont("setting_category");
                    color:
                    {
                        if(!control.enabled)
                        {
                            return Theme.getColor("setting_category_disabled_text");
                        }
                        else if((control.hovered || control.activeFocus) && control.checkable && control.checked)
                        {
                            return Theme.getColor("setting_category_active_hover_text");
                        }
                        else if(control.pressed || (control.checkable && control.checked))
                        {
                            return Theme.getColor("setting_category_active_text");
                        }
                        else if(control.hovered || control.activeFocus)
                        {
                            return Theme.getColor("setting_category_hover_text");
                        }
                        else
                        {
                            return Theme.getColor("setting_category_text");
                        }
                    }
                    fontSizeMode: Text.HorizontalFit;
                    minimumPointSize: 8
                }
                UM.RecolorImage {
                    id: category_arrow
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    anchors.rightMargin: Theme.getSize("default_margin").width * 3 - width / 2
                    width: Theme.getSize("standard_arrow").width
                    height: Theme.getSize("standard_arrow").height
                    sourceSize.width: width
                    sourceSize.height: width
                    color:
                    {
                        if(!control.enabled)
                        {
                            return Theme.getColor("setting_category_disabled_text");
                        }
                        else if((control.hovered || control.activeFocus) && control.checkable && control.checked)
                        {
                            return Theme.getColor("setting_category_active_hover_text");
                        }
                        else if(control.pressed || (control.checkable && control.checked))
                        {
                            return Theme.getColor("setting_category_active_text");
                        }
                        else if(control.hovered || control.activeFocus)
                        {
                            return Theme.getColor("setting_category_hover_text");
                        }
                        else
                        {
                            return Theme.getColor("setting_category_text");
                        }
                    }
                    source: control.checked ? Theme.getIcon("arrow_bottom") : Theme.getIcon("arrow_left")
                }
            }
        }
    }

    property Component scrollview: Component {
        ScrollViewStyle {
            decrementControl: Item { }
            incrementControl: Item { }

            transientScrollBars: false

            scrollBarBackground: Rectangle {
                implicitWidth: Theme.getSize("scrollbar").width
                radius: implicitWidth / 2
                color: Theme.getColor("scrollbar_background");
            }

            handle: Rectangle {
                id: scrollViewHandle
                implicitWidth: Theme.getSize("scrollbar").width;
                radius: implicitWidth / 2

                color: styleData.pressed ? Theme.getColor("scrollbar_handle_down") : styleData.hovered ? Theme.getColor("scrollbar_handle_hover") : Theme.getColor("scrollbar_handle");
                Behavior on color { ColorAnimation { duration: 50; } }
            }
        }
    }

    property Component combobox: Component {
        ComboBoxStyle {

            background: Rectangle {
                implicitHeight: Theme.getSize("setting_control").height;
                implicitWidth: Theme.getSize("setting_control").width;

                color: control.hovered ? UM.Theme.getColor("setting_control_highlight") : UM.Theme.getColor("setting_control")
                Behavior on color { ColorAnimation { duration: 50; } }

                border.width: Theme.getSize("default_lining").width;
                border.color: control.hovered ? Theme.getColor("setting_control_border_highlight") : Theme.getColor("setting_control_border");
            }

            label: Item {

                Label {
                    anchors.left: parent.left;
                    anchors.leftMargin: Theme.getSize("default_lining").width
                    anchors.right: downArrow.left;
                    anchors.rightMargin: Theme.getSize("default_lining").width;
                    anchors.verticalCenter: parent.verticalCenter;

                    text: control.currentText;
                    font: Theme.getFont("default");
                    color: !enabled ? Theme.getColor("setting_control_disabled_text") : Theme.getColor("setting_control_text");

                    elide: Text.ElideRight;
                    verticalAlignment: Text.AlignVCenter;
                }

                UM.RecolorImage {
                    id: downArrow
                    anchors.right: parent.right;
                    anchors.rightMargin: Theme.getSize("default_lining").width * 2;
                    anchors.verticalCenter: parent.verticalCenter;

                    source: Theme.getIcon("arrow_bottom")
                    width: Theme.getSize("standard_arrow").width
                    height: Theme.getSize("standard_arrow").height
                    sourceSize.width: width + 5
                    sourceSize.height: width + 5

                    color: Theme.getColor("setting_control_text");
                }
            }
        }
    }

    // Combobox with items with colored rectangles
    property Component combobox_color: Component {

        ComboBoxStyle {

            background: Rectangle {
                color: !enabled ? UM.Theme.getColor("setting_control_disabled") : control._hovered ? UM.Theme.getColor("setting_control_highlight") : UM.Theme.getColor("setting_control")
                border.width: UM.Theme.getSize("default_lining").width
                border.color: !enabled ? UM.Theme.getColor("setting_control_disabled_border") : control._hovered ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_border")
            }

            label: Item {

                Label {
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

                Rectangle {
                    id: swatch
                    height: UM.Theme.getSize("setting_control").height / 2
                    width: height
                    anchors.right: downArrow.left
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.margins: UM.Theme.getSize("default_margin").width / 4
                    radius: width / 2
                    border.width: UM.Theme.getSize("default_lining").width
                    border.color: UM.Theme.getColor("lining")
                    color: (control.color_override !== "") ? control.color_override : control.color
                }

                UM.RecolorImage {
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
    }

    property Component checkbox: Component {
        CheckBoxStyle {
            background: Item { }
            indicator: Rectangle {
                implicitWidth:  Theme.getSize("checkbox").width;
                implicitHeight: Theme.getSize("checkbox").height;

                color: (control.hovered || control._hovered) ? Theme.getColor("checkbox_hover") : Theme.getColor("checkbox");
                Behavior on color { ColorAnimation { duration: 50; } }

                radius: control.exclusiveGroup ? Theme.getSize("checkbox").width / 2 : 0

                border.width: Theme.getSize("default_lining").width;
                border.color: (control.hovered || control._hovered) ? Theme.getColor("checkbox_border_hover") : Theme.getColor("checkbox_border");

                UM.RecolorImage {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: parent.width/2.5
                    height: parent.height/2.5
                    sourceSize.width: width
                    sourceSize.height: width
                    color: Theme.getColor("checkbox_mark")
                    source: control.exclusiveGroup ? Theme.getIcon("dot") : Theme.getIcon("check")
                    opacity: control.checked
                    Behavior on opacity { NumberAnimation { duration: 100; } }
                }
            }
            label: Label {
                text: control.text;
                color: Theme.getColor("checkbox_text");
                font: Theme.getFont("default");
            }
        }
    }

    property Component slider: Component {
        SliderStyle {
            groove: Rectangle {
                implicitWidth: control.width;
                implicitHeight: Theme.getSize("slider_groove").height;

                color: Theme.getColor("slider_groove");
                border.width: Theme.getSize("default_lining").width;
                border.color: Theme.getColor("slider_groove_border");

                radius: width / 2;

                Rectangle {
                    anchors {
                        left: parent.left;
                        top: parent.top;
                        bottom: parent.bottom;
                    }
                    color: Theme.getColor("slider_groove_fill");
                    width: (control.value / (control.maximumValue - control.minimumValue)) * parent.width;
                    radius: width / 2;
                }
            }
            handle: Rectangle {
                width: Theme.getSize("slider_handle").width;
                height: Theme.getSize("slider_handle").height;
                color: control.hovered ? Theme.getColor("slider_handle_hover") : Theme.getColor("slider_handle");
                border.width: Theme.getSize("default_lining").width
                border.color: control.hovered ? Theme.getColor("slider_handle_hover_border") : Theme.getColor("slider_handle_border")
                radius: Theme.getSize("slider_handle").width / 2; //Round.
                Behavior on color { ColorAnimation { duration: 50; } }
            }
        }
    }

    property Component text_field: Component {
        TextFieldStyle {
            textColor: Theme.getColor("setting_control_text");
            placeholderTextColor: Theme.getColor("setting_control_text")
            font: Theme.getFont("default");

            background: Rectangle
            {
                implicitHeight: control.height;
                implicitWidth: control.width;

                border.width: Theme.getSize("default_lining").width;
                border.color: control.hovered ? Theme.getColor("setting_control_border_highlight") : Theme.getColor("setting_control_border");

                color: Theme.getColor("setting_validation_ok");

                Label {
                    anchors.right: parent.right;
                    anchors.rightMargin: Theme.getSize("setting_unit_margin").width;
                    anchors.verticalCenter: parent.verticalCenter;

                    text: control.unit ? control.unit : ""
                    color: Theme.getColor("setting_unit");
                    font: Theme.getFont("default");
                }
            }
        }
    }

    property Component sidebar_action_button: Component {
        ButtonStyle
        {
            background: Rectangle
            {
                border.width: UM.Theme.getSize("default_lining").width
                border.color:
                {
                    if(!control.enabled)
                        return UM.Theme.getColor("action_button_disabled_border");
                    else if(control.pressed)
                        return UM.Theme.getColor("action_button_active_border");
                    else if(control.hovered)
                        return UM.Theme.getColor("action_button_hovered_border");
                    else
                        return UM.Theme.getColor("action_button_border");
                }
                color:
                {
                    if(!control.enabled)
                        return UM.Theme.getColor("action_button_disabled");
                    else if(control.pressed)
                        return UM.Theme.getColor("action_button_active");
                    else if(control.hovered)
                        return UM.Theme.getColor("action_button_hovered");
                    else
                        return UM.Theme.getColor("action_button");
                }
                Behavior on color { ColorAnimation { duration: 50; } }

                implicitWidth: actualLabel.contentWidth + (UM.Theme.getSize("sidebar_margin").width * 2)

                Label
                {
                    id: actualLabel
                    anchors.centerIn: parent
                    color:
                    {
                        if(!control.enabled)
                            return UM.Theme.getColor("action_button_disabled_text");
                        else if(control.pressed)
                            return UM.Theme.getColor("action_button_active_text");
                        else if(control.hovered)
                            return UM.Theme.getColor("action_button_hovered_text");
                        else
                            return UM.Theme.getColor("action_button_text");
                    }
                    font: UM.Theme.getFont("action_button")
                    text: control.text
                }
            }
            label: Item { }
        }
    }
}
