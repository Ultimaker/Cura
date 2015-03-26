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
                color: control.hovered ? UM.Theme.colors.text_hover : down ? UM.Theme.colors.text_pressed : UM.Theme.colors.text;

                text: control.text;
            }
        }
    }

    property Component tool_button: Component {
        ButtonStyle {
            background: Rectangle {
                implicitWidth: UM.Theme.sizes.button.width;
                implicitHeight: UM.Theme.sizes.button.height;
                color: UM.Theme.colors.primary;
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
}
