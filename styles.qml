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
            }
        }
    }

    property Component tool_button: Component {
        ButtonStyle {
            background: UM.AngledCornerRectangle {
                property bool down: control.pressed || (control.checkable && control.checked);

                implicitWidth: UM.Theme.sizes.button.width;
                implicitHeight: UM.Theme.sizes.button.height;
                color: down ? UM.Theme.colors.button_down : control.hovered ? UM.Theme.colors.button_hover : UM.Theme.colors.button;
                Behavior on color { ColorAnimation { duration: 50; } }
                cornerSize: UM.Theme.sizes.default_margin.width;
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

    property Component sidebar_category: Component {
        ButtonStyle {
            background: UM.AngledCornerRectangle {
                property bool down: control.pressed || (control.checkable && control.checked);
                implicitHeight: UM.Theme.sizes.section.height;
                color: {
                    if(!control.enabled) {
                        return UM.Theme.colors.button_disabled;
                    } else if(down) {
                        return UM.Theme.colors.button_down;
                    } else if(control.hovered) {
                        return UM.Theme.colors.button_hover;
                    } else {
                        return UM.Theme.colors.button;
                    }
                }
                Behavior on color { ColorAnimation { duration: 50; } }
                cornerSize: UM.Theme.sizes.default_margin.width;
            }
            label: Row {
                anchors.fill: parent;
                anchors.margins: UM.Theme.sizes.default_margin.width;
                spacing: UM.Theme.sizes.default_margin.width;
                Image { anchors.verticalCenter: parent.verticalCenter; source: control.iconSource; }
                Label { anchors.verticalCenter: parent.verticalCenter; text: control.text; font: UM.Theme.fonts.large; color: UM.Theme.colors.button_text }
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

        validationErrorColor: Qt.rgba(1.0, 0.0, 0.0, 1.0);
        validationWarningColor: Qt.rgba(1.0, 1.0, 0.0, 1.0);
        validationOkColor: Qt.rgba(1.0, 1.0, 1.0, 1.0);

        unitRightMargin: UM.Theme.sizes.setting_unit_margin.width;
        unitColor: UM.Theme.colors.setting_unit;
        unitFont: UM.Theme.fonts.default;
    }
}
