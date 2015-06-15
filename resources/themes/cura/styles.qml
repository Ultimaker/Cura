// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.0 as UM

QtObject {
    property Component sidebar_header_button: Component {
        ButtonStyle {
            background: Item {
                Label {
                    anchors.right: parent.right;
                    anchors.top: parent.top;

                    text: "▼";

                    property bool down: control.pressed || (control.checkable && control.checked);
                    color: down ? UM.Theme.colors.text_pressed : control.hovered ? UM.Theme.colors.text_hover : UM.Theme.colors.text;
                }
            }

            label: Label {
                property bool down: control.pressed || (control.checkable && control.checked);

                font: UM.Theme.fonts.sidebar_header;
                color: down ? UM.Theme.colors.text_pressed : control.hovered ? UM.Theme.colors.text_hover : UM.Theme.colors.text;

                text: control.text;

                elide: Text.ElideRight;
            }
        }
    }

     property Component open_file_button: Component {
        ButtonStyle {
            background: Item {
                implicitWidth: UM.Theme.sizes.button.width;
                implicitHeight: UM.Theme.sizes.button.height;

                Rectangle {
                    anchors.bottom: parent.verticalCenter;
                    width: parent.width;
                    height: control.hovered ? parent.height / 2 + label.height : 0;
                    Behavior on height { NumberAnimation { duration: 100; } }

                    opacity: control.hovered ? 1.0 : 0.0;
                    Behavior on opacity { NumberAnimation { duration: 100; } }

                    Label {
                        id: label;
                        anchors.horizontalCenter: parent.horizontalCenter;
                        text: control.text.replace("&", "");
                        font: UM.Theme.fonts.button_tooltip;
                        color: UM.Theme.colors.button_tooltip_text;
                    }
                }

                UM.AngledCornerRectangle {
                    anchors.fill: parent;
                    color: {
                        if(control.hovered) {
                            return UM.Theme.colors.button_active_hover;
                        } else {
                            return UM.Theme.colors.button_active;
                        }
                    }
                    Behavior on color { ColorAnimation { duration: 50; } }
                    cornerSize: UM.Theme.sizes.default_margin.width;
                }
            }

            label: Item {
                Image {
                    anchors.centerIn: parent;

                    source: control.iconSource;
                    width: UM.Theme.sizes.button_icon.width;
                    height: UM.Theme.sizes.button_icon.height;

                    sourceSize: UM.Theme.sizes.button_icon;
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
                    anchors.bottom: parent.verticalCenter;

                    width: parent.width;
                    height: control.hovered ? parent.height / 2 + label.height : 0;
                    Behavior on height { NumberAnimation { duration: 100; } }

                    opacity: control.hovered ? 1.0 : 0.0;
                    Behavior on opacity { NumberAnimation { duration: 100; } }

                    Label {
                        id: label
                        anchors.horizontalCenter: parent.horizontalCenter;
                        text: control.text.replace("&", "");
                        font: UM.Theme.fonts.button_tooltip;
                        color: UM.Theme.colors.button_tooltip_text;
                    }
                }

                UM.AngledCornerRectangle {
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
                    cornerSize: UM.Theme.sizes.default_margin.width;
                }
            }

            label: Item {
                Image {
                    anchors.centerIn: parent;

                    source: control.iconSource;
                    width: UM.Theme.sizes.button_icon.width;
                    height: UM.Theme.sizes.button_icon.height;

                    sourceSize: UM.Theme.sizes.button_icon;
                }
            }
        }
    }


    property Component progressbar: Component{
        ProgressBarStyle {
            background: UM.AngledCornerRectangle {
                anchors.fill: parent
                anchors.left: parent.left
                implicitWidth: UM.Theme.sizes.progressbar.width
                implicitHeight: UM.Theme.sizes.progressbar.height
                color: "transparent"
            }
            progress: UM.AngledCornerRectangle {
                anchors.left: parent.left
                anchors.fill: parent
                cornerSize: UM.Theme.sizes.progressbar_control.height
                color: UM.Theme.colors.progressbar_background
                Item {
                    anchors.fill: parent
                    anchors.margins: UM.Theme.sizes.progressbar_margin.width
                    visible: control.indeterminate
                    Row {
                        Repeater {
                            UM.AngledCornerRectangle {
                                cornerSize: UM.Theme.sizes.progressbar_control.height
                                color: UM.Theme.colors.progressbar_control
                                width: UM.Theme.sizes.progressbar_control.width
                                height: UM.Theme.sizes.progressbar_control.height
                            }
                            model: 1
                        }
                        SequentialAnimation on x {
                            id: xAnim
                            property int animEndPoint: UM.Theme.sizes.progressbar.width - UM.Theme.sizes.progressbar_control.width
                            running: control.indeterminate
                            loops: Animation.Infinite
                            NumberAnimation { from: 0; to: xAnim.animEndPoint; duration: 2000;}
                            NumberAnimation { from: xAnim.animEndPoint; to: 0; duration: 2000;}
                        }
                    }
                }
            }
        }
    }

    property Component sidebar_category: Component {
        ButtonStyle {
            background: UM.AngledCornerRectangle {
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
                cornerSize: UM.Theme.sizes.default_margin.width;
            }
            label: Row {
                anchors.fill: parent;
                anchors.margins: UM.Theme.sizes.default_margin.width;
                spacing: UM.Theme.sizes.default_margin.width;

                Image {
                    anchors.verticalCenter: parent.verticalCenter;
                    source: control.iconSource;
                    width: UM.Theme.sizes.section_icon.width;
                    height: UM.Theme.sizes.section_icon.height;
                }

                Label {
                    anchors.verticalCenter: parent.verticalCenter;
                    text: control.text;
                    font: UM.Theme.fonts.setting_category;
                    color: UM.Theme.colors.setting_category_text;
                }
            }
        }
    }

    property Component scrollview: Component {
        ScrollViewStyle {
            decrementControl: Item { }
            incrementControl: Item { }

            transientScrollBars: false

            scrollBarBackground: UM.AngledCornerRectangle {
                implicitWidth: UM.Theme.sizes.scrollbar.width;

                cornerSize: UM.Theme.sizes.scrollbar.width;

                color: UM.Theme.colors.scrollbar_background;
            }

            handle: UM.AngledCornerRectangle {
                implicitWidth: UM.Theme.sizes.scrollbar.width;

                cornerSize: UM.Theme.sizes.scrollbar.width;

                color: styleData.pressed ? UM.Theme.colors.scrollbar_handle_down : styleData.hovered ? UM.Theme.colors.scrollbar_handle_hover : UM.Theme.colors.scrollbar_handle;
                Behavior on color { ColorAnimation { duration: 50; } }
            }
        }
    }

    property variant setting_item: UM.SettingItemStyle {
        labelFont: UM.Theme.fonts.default;
        labelColor: UM.Theme.colors.setting_label;

        spacing: UM.Theme.sizes.default_margin.width;
        fixedHeight: UM.Theme.sizes.setting.height;

        controlWidth: UM.Theme.sizes.setting_control.width;
        controlRightMargin: UM.Theme.sizes.setting_control_margin.width;
        controlBorderWidth: 1;
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
