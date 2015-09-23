// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.0 as UM

QtObject {
    property Component sidebar_header_button: Component {
        ButtonStyle {
            background: Rectangle {
                color: UM.Theme.colors.setting_control
                border.width: 1
                border.color: UM.Theme.colors.setting_control_border
                UM.RecolorImage {
                    id: downArrow
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    anchors.rightMargin: UM.Theme.sizes.default_margin.width
                    width: UM.Theme.sizes.standard_arrow.width
                    height: UM.Theme.sizes.standard_arrow.height
                    sourceSize.width: width
                    sourceSize.height: width
                    color: UM.Theme.colors.setting_category_text
                    source: UM.Theme.icons.arrow_bottom
                }
                Label {
                    id: sidebarComboBoxLabel
                    //property bool down: control.pressed || (control.checkable && control.checked);
                    color: UM.Theme.colors.setting_control_text
                    text: control.text;
                    elide: Text.ElideRight;
                    anchors.left: parent.left;
                    anchors.leftMargin: UM.Theme.sizes.setting_unit_margin.width
                    anchors.right: separationLine.left;
                    anchors.verticalCenter: parent.verticalCenter;
                    font: UM.Theme.fonts.default
                }
                Rectangle{
                    id: separationLine
                    width: 1
                    height: UM.Theme.sizes.setting_control.height
                    color: UM.Theme.colors.setting_control_border
                    anchors.right: downArrow.left
                    anchors.rightMargin: UM.Theme.sizes.setting_unit_margin.width + downArrow.width/2
                    anchors.top: parent.top
                    z: parent.z + 1
                }
            }
            label: Label{}
        }
    }

    property Component open_file_button: Component {
        ButtonStyle {
            background: Item{
                implicitWidth: UM.Theme.sizes.button.width;
                implicitHeight: UM.Theme.sizes.button.height;
                Rectangle {
                    anchors.left: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    color: UM.Theme.colors.button_text
                    width: control.hovered ? openFileLabel.width : 0;
                    height: openFileLabel.height
                    Behavior on width { NumberAnimation { duration: 100; } }
                    opacity: control.hovered ? 1.0 : 0.0;
                    Behavior on opacity { NumberAnimation { duration: 100; } }
                    Label {
                        id: openFileLabel
                        anchors.bottom: parent.bottom
                        text: control.text
                        font: UM.Theme.fonts.button_tooltip;
                        color: UM.Theme.colors.button_tooltip_text;
                    }
                }
                Rectangle {
                    anchors.fill: parent;
                    color: control.hovered ? UM.Theme.colors.load_save_button_hover : UM.Theme.colors.load_save_button
                    Behavior on color { ColorAnimation { duration: 50; } }
                }
            }
            label: Item {
                Image {
                    anchors.centerIn: parent;
                    source: control.iconSource;
                    width: UM.Theme.sizes.button_icon.width;
                    height: UM.Theme.sizes.button_icon.height;
                    sourceSize: UM.Theme.sizes.button_icon
                }
            }
        }
    }

    property Component tool_button: Component {
        ButtonStyle {
            background: Item {
                implicitWidth: UM.Theme.sizes.button.width;
                implicitHeight: UM.Theme.sizes.button.height;

                Rectangle {
                    id: tool_button_background
                    anchors.left: control.verticalTooltip ? parent.left : parent.right
                    anchors.verticalCenter: control.verticalTooltip ?  undefined : parent.verticalCenter
                    anchors.top: control.verticalTooltip ? parent.bottom : undefined
                    opacity: control.hovered ? 1.0 : 0.0;

                    width: {
                        if (control.verticalTooltip == true){
                            if (label.width > parent.width)
                                return label.width
                            else
                                return parent.width
                        }
                        else {
                            if (control.hovered)
                                return label.width
                            else
                                return 0
                        }
                    }
                    height: !control.verticalTooltip ? label.height : control.hovered ? label.height: 0

                    Behavior on width { NumberAnimation { duration: 100; } }
                    Behavior on height { NumberAnimation { duration: 100; } }
                    Behavior on opacity { NumberAnimation { duration: 100; } }

                    Label {
                        id: label
                        anchors.bottom: parent.bottom
                        text: control.text
                        font: UM.Theme.fonts.button_tooltip;
                        color: UM.Theme.colors.button_tooltip_text;
                    }
                }

                Rectangle {
                    id: buttonFace;

                    anchors.fill: parent;
                    property bool down: control.pressed || (control.checkable && control.checked);

                    color: {
                        if(control.checkable && control.checked && control.hovered) {
                            return UM.Theme.colors.button_active_hover;
                        } else if(control.pressed || (control.checkable && control.checked)) {
                            return UM.Theme.colors.button_active;
                        } else if(control.hovered) {
                            return UM.Theme.colors.button_hover;
                        } else {
                            return UM.Theme.colors.button;
                        }
                    }
                    Behavior on color { ColorAnimation { duration: 50; } }

                    Label {
                        id: tool_button_arrow
                        opacity: !control.enabled ? 0.4 : 1.0
                        anchors.right: parent.right;
                        anchors.rightMargin: (UM.Theme.sizes.button.width - UM.Theme.sizes.button_icon.width - tool_button_arrow.width) / 2
                        anchors.verticalCenter: parent.verticalCenter;
                        text: "▼";
                        font: UM.Theme.fonts.small;
                        visible: control.menu != null;
                        color: UM.Theme.colors.button_text
                    }
                }
            }

            label: Item {
                Image {
                    anchors.centerIn: parent;
                    opacity: !control.enabled ? 0.4 : 1.0
                    source: control.iconSource;
                    width: UM.Theme.sizes.button_icon.width;
                    height: UM.Theme.sizes.button_icon.height;

                    sourceSize: UM.Theme.sizes.button_icon
                }
            }
        }
    }
    property Component tool_button_panel: Component {
        ButtonStyle {
            background: Item {
                implicitWidth: UM.Theme.sizes.button.width;
                implicitHeight: UM.Theme.sizes.button.height;

                Rectangle {
                    id: tool_button_background
                    anchors.top: parent.verticalCenter;

                    width: parent.width;
                    height: control.hovered ? parent.height / 2 + label.height : 0;
                    Behavior on height { NumberAnimation { duration: 100; } }

                    opacity: control.hovered ? 1.0 : 0.0;
                    Behavior on opacity { NumberAnimation { duration: 100; } }

                    Label {
                        id: label
                        anchors.bottom: parent.bottom
                        text: control.text
                        width: UM.Theme.sizes.button.width;
                        wrapMode: Text.WordWrap
                        font: UM.Theme.fonts.button_tooltip;
                        color: UM.Theme.colors.button_tooltip_text;
                    }
                }

                Rectangle {
                    id: buttonFace;

                    anchors.fill: parent;

                    property bool down: control.pressed || (control.checkable && control.checked);

                    color: {
                        if(!control.enabled) {
                            return UM.Theme.colors.button_disabled;
                        } else if(control.checkable && control.checked && control.hovered) {
                            return UM.Theme.colors.button_active_hover;
                        } else if(control.pressed || (control.checkable && control.checked)) {
                            return UM.Theme.colors.button_active;
                        } else if(control.hovered) {
                            return UM.Theme.colors.button_hover;
                        } else {
                            return UM.Theme.colors.button;
                        }
                    }
                    Behavior on color { ColorAnimation { duration: 50; } }
                }
            }

            label: Item {
                Image {
                    anchors.centerIn: parent;

                    source: control.iconSource;
                    width: UM.Theme.sizes.button_icon.width;
                    height: UM.Theme.sizes.button_icon.height;

                    sourceSize: UM.Theme.sizes.button_icon
                }
            }
        }
    }


    property Component progressbar: Component{
        ProgressBarStyle {
            background:Rectangle {
                implicitWidth: UM.Theme.sizes.message.width - (UM.Theme.sizes.default_margin.width * 2)
                implicitHeight: UM.Theme.sizes.progressbar.height
                color: UM.Theme.colors.progressbar_background
            }
            progress: Rectangle {
                color: control.indeterminate ? "transparent" : UM.Theme.colors.progressbar_control
                Rectangle{
                    color: UM.Theme.colors.progressbar_control
                    width: UM.Theme.sizes.progressbar_control.width
                    height: UM.Theme.sizes.progressbar_control.height
                    visible: control.indeterminate

                    SequentialAnimation on x {
                        id: xAnim
                        property int animEndPoint: UM.Theme.sizes.message.width - (UM.Theme.sizes.default_margin.width * 2) - UM.Theme.sizes.progressbar_control.width
                        running: control.indeterminate
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
                implicitHeight: UM.Theme.sizes.section.height;
                color: {
                    if(control.color) {
                        return control.color;
                    } else if(!control.enabled) {
                        return UM.Theme.colors.setting_category_disabled;
                    } else if(control.hovered && control.checkable && control.checked) {
                        return UM.Theme.colors.setting_category_active_hover;
                    } else if(control.pressed || (control.checkable && control.checked)) {
                        return UM.Theme.colors.setting_category_active;
                    } else if(control.hovered) {
                        return UM.Theme.colors.setting_category_hover;
                    } else {
                        return UM.Theme.colors.setting_category;
                    }
                }
                Behavior on color { ColorAnimation { duration: 50; } }
            }
            label: Item {
                anchors.fill: parent;
                anchors.left: parent.left
                Item{
                    id: icon;
                    anchors.left: parent.left
                    height: parent.height
                    width: UM.Theme.sizes.section_icon_column.width
                    UM.RecolorImage {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                        color: UM.Theme.colors.setting_category_text
                        source: control.iconSource;
                        width: UM.Theme.sizes.section_icon.width;
                        height: UM.Theme.sizes.section_icon.height;
                        sourceSize.width: width + 15
                        sourceSize.height: width + 15
                    }
                }

                Label {
                    anchors {
                        left: icon.right;
                        right: parent.right;
                        verticalCenter: parent.verticalCenter;
                    }
                    text: control.text;
                    font: UM.Theme.fonts.setting_category;
                    color: UM.Theme.colors.setting_category_text;
                    fontSizeMode: Text.HorizontalFit;
                    minimumPointSize: 8
                }
                UM.RecolorImage {
                    id: category_arrow
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    anchors.rightMargin: UM.Theme.sizes.default_margin.width * 2 - width / 2
                    width: UM.Theme.sizes.standard_arrow.width
                    height: UM.Theme.sizes.standard_arrow.height
                    sourceSize.width: width
                    sourceSize.height: width
                    color: UM.Theme.colors.setting_category_text
                    source: control.checked ? UM.Theme.icons.arrow_top : UM.Theme.icons.arrow_bottom
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
                implicitWidth: UM.Theme.sizes.scrollbar.width
                color: UM.Theme.colors.scrollbar_background;
            }

            handle: Rectangle {
                id: scrollViewHandle
                implicitWidth: UM.Theme.sizes.scrollbar.width;

                color: styleData.pressed ? UM.Theme.colors.scrollbar_handle_down : styleData.hovered ? UM.Theme.colors.scrollbar_handle_hover : UM.Theme.colors.scrollbar_handle;
                Behavior on color { ColorAnimation { duration: 50; } }
            }
        }
    }

    property variant setting_item: UM.SettingItemStyle {
        labelFont: UM.Theme.fonts.default;
        labelColor: UM.Theme.colors.setting_control_text;

        spacing: UM.Theme.sizes.default_lining.height;
        fixedHeight: UM.Theme.sizes.setting.height;

        controlWidth: UM.Theme.sizes.setting_control.width;
        controlRightMargin: UM.Theme.sizes.setting_control_margin.width;
        controlColor: UM.Theme.colors.setting_control;
        controlHighlightColor: UM.Theme.colors.setting_control_highlight;
        controlBorderColor: UM.Theme.colors.setting_control_border;
        controlTextColor: UM.Theme.colors.setting_control_text;
        controlFont: UM.Theme.fonts.default;

        validationErrorColor: UM.Theme.colors.setting_validation_error;
        validationWarningColor: UM.Theme.colors.setting_validation_warning;
        validationOkColor: UM.Theme.colors.setting_validation_ok;

        unitRightMargin: UM.Theme.sizes.setting_unit_margin.width;
        unitColor: UM.Theme.colors.setting_unit;
        unitFont: UM.Theme.fonts.default;
    }

    property Component checkbox: Component {
        CheckBoxStyle {
            background: Item { }
            indicator: Rectangle {
                implicitWidth:  UM.Theme.sizes.checkbox.width;
                implicitHeight: UM.Theme.sizes.checkbox.height;

                color: control.hovered ? UM.Theme.colors.checkbox_hover : UM.Theme.colors.checkbox;
                Behavior on color { ColorAnimation { duration: 50; } }

                border.width: 1
                border.color: UM.Theme.colors.checkbox_border;

                Label {
                    anchors.centerIn: parent;
                    color: UM.Theme.colors.checkbox_mark;

                    text: "✓";

                    opacity: control.checked ? 1 : 0;
                    Behavior on opacity { NumberAnimation { duration: 100; } }
                }
            }
            label: Label {
                text: control.text;
                color: UM.Theme.colors.checkbox_text;
                font: UM.Theme.fonts.default;
            }
        }
    }

    property Component slider: Component {
        SliderStyle {
            groove: Rectangle {
                implicitWidth: control.width;
                implicitHeight: UM.Theme.sizes.slider_groove.height;

                color: UM.Theme.colors.slider_groove;
                border.width: 1;
                border.color: UM.Theme.colors.slider_groove_border;

                Rectangle {
                    anchors {
                        left: parent.left;
                        top: parent.top;
                        bottom: parent.bottom;
                    }
                    color: UM.Theme.colors.slider_groove_fill;
                    width: (control.value / (control.maximumValue - control.minimumValue)) * parent.width;
                }
            }
            handle: Rectangle {
                width: UM.Theme.sizes.slider_handle.width;
                height: UM.Theme.sizes.slider_handle.height;
                color: control.hovered ? UM.Theme.colors.slider_handle_hover : UM.Theme.colors.slider_handle;
                Behavior on color { ColorAnimation { duration: 50; } }
            }
        }
    }

    property Component layerViewSlider: Component {
        SliderStyle {
            groove: Rectangle {
                id: layerSliderGroove
                implicitWidth: control.width;
                implicitHeight: UM.Theme.sizes.slider_groove.height;

                color: UM.Theme.colors.slider_groove;
                border.width: 1;
                border.color: UM.Theme.colors.slider_groove_border;
                Rectangle {
                    anchors {
                        left: parent.left;
                        top: parent.top;
                        bottom: parent.bottom;
                    }
                    color: UM.Theme.colors.slider_groove_fill;
                    width: (control.value / (control.maximumValue - control.minimumValue)) * parent.width;
                }
            }
            handle: Rectangle {
                id: layerSliderControl
                width: UM.Theme.sizes.slider_handle.width;
                height: UM.Theme.sizes.slider_handle.height;
                color: control.hovered ? UM.Theme.colors.slider_handle_hover : UM.Theme.colors.slider_handle;
                Behavior on color { ColorAnimation { duration: 50; } }
                TextField {
                    id: valueLabel
                    property int unremovableSpacing: 5
                    property string maxValue: control.maximumValue + 1
                    placeholderText: control.value + 1
                    onEditingFinished: {
                        if (valueLabel.text != ''){
                            control.value = valueLabel.text - 1
                            valueLabel.text = ''
                            valueLabel.focus = false
                        }

                    }
                    validator: IntValidator {bottom: 1; top: control.maximumValue + 1;}
                    visible: UM.LayerView.getLayerActivity && Printer.getPlatformActivity ? true : false
                    anchors.bottom: layerSliderControl.bottom
                    anchors.right: layerSliderControl.left
                    anchors.rightMargin: valueLabel.unremovableSpacing / 2
                    anchors.bottomMargin: parent.width + (UM.Theme.sizes.default_margin.width / 2)
                    transformOrigin: Item.BottomRight
                    rotation: 90
                    style: TextFieldStyle{
                        textColor: UM.Theme.colors.setting_control_text;
                        font: UM.Theme.fonts.default;
                        background: Rectangle {
                            radius: 0
                            implicitWidth: control.maxValue.length * valueLabel.font.pixelSize
                            implicitHeight: UM.Theme.sizes.slider_handle.height + valueLabel.unremovableSpacing
                            border.width: 1;
                            border.color: UM.Theme.colors.slider_groove_border;
                        }
                    }
                }
            }
        }
    }

    property Component text_field: Component {
        TextFieldStyle {
            textColor: UM.Theme.colors.setting_control_text;
            font: UM.Theme.fonts.default;

            background: Rectangle
            {
                implicitHeight: control.height;
                implicitWidth: control.width;

                border.width: 1;
                border.color: UM.Theme.colors.setting_control_border;

                color: UM.Theme.colors.setting_validation_ok;

                Label {
                    anchors.right: parent.right;
                    anchors.rightMargin: UM.Theme.sizes.setting_unit_margin.width;
                    anchors.verticalCenter: parent.verticalCenter;

                    text: control.unit ? control.unit : ""
                    color: UM.Theme.colors.setting_unit;
                    font: UM.Theme.fonts.default;
                }
            }
        }
    }
}
