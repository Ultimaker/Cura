import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.0 as UM

QtObject {
    property Component sidebar_header_button: Component {
        ButtonStyle {
            background: Item {
                Image {
                    anchors.right: parent.right;
                    anchors.verticalCenter: parent.verticalCenter;

                    source: UM.Theme.icons.down_arrow;
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

    property Component category: Component {
        ButtonStyle {
            background: UM.AngledCornerRectangle {
                property bool down: control.pressed || (control.checkable && control.checked);
                color: down ? UM.Theme.colors.button_down : control.hovered ? UM.Theme.colors.button_hover : UM.Theme.colors.button;
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
}
