import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Button {
    id: base;

    property Action saveAction;

    property real progress: UM.Backend.progress;
    Behavior on progress { NumberAnimation { duration: 250; } }

    enabled: progress >= 0.95;

    iconSource: UM.Theme.icons[Printer.outputDeviceIcon];

    style: ButtonStyle {
        background: UM.AngledCornerRectangle {
            implicitWidth: control.width;
            implicitHeight: control.height;

            color: UM.Theme.colors.save_button_border;
            cornerSize: UM.Theme.sizes.default_margin.width;

            UM.AngledCornerRectangle {
                anchors.fill: parent;
                anchors.margins: UM.Theme.sizes.save_button_border.width;
                cornerSize: UM.Theme.sizes.default_margin.width;
                color: UM.Theme.colors.save_button;
            }

            UM.AngledCornerRectangle {
                anchors {
                    left: parent.left;
                    top: parent.top;
                    bottom: parent.bottom;
                }

                width: Math.max(parent.height + (parent.width - parent.height) * control.progress, parent.height);
                cornerSize: UM.Theme.sizes.default_margin.width;

                color: !control.enabled ? UM.Theme.colors.save_button_inactive : control.hovered ? UM.Theme.colors.save_button_active_hover : UM.Theme.colors.save_button_active;
                Behavior on color { ColorAnimation { duration: 50; } }
            }

            UM.AngledCornerRectangle {
                anchors.left: parent.left;
                width: parent.height + UM.Theme.sizes.save_button_border.width;
                height: parent.height;
                cornerSize: UM.Theme.sizes.default_margin.width;
                color: UM.Theme.colors.save_button;
            }

            UM.AngledCornerRectangle {
                anchors.left: parent.left;
                width: parent.height + UM.Theme.sizes.save_button_border.width;
                height: parent.height;
                cornerSize: UM.Theme.sizes.default_margin.width;

                color: UM.Theme.colors.save_button;
            }

            UM.AngledCornerRectangle {
                id: icon;

                anchors.left: parent.left;
                width: parent.height;
                height: parent.height;
                cornerSize: UM.Theme.sizes.default_margin.width;
                color: !control.enabled ? UM.Theme.colors.save_button_inactive : control.hovered ? UM.Theme.colors.save_button_active_hover : UM.Theme.colors.save_button_active;
                Behavior on color { ColorAnimation { duration: 50; } }

                Image {
                    anchors.centerIn: parent;

                    width: UM.Theme.sizes.button_icon.width;
                    height: UM.Theme.sizes.button_icon.height;

                    sourceSize.width: width;
                    sourceSize.height: height;

                    source: control.iconSource;
                }
            }
        }

        label: Label {
            id: label;
            anchors.top: parent.top;
            anchors.topMargin: UM.Theme.sizes.save_button_label_margin.height;
            anchors.left: parent.left;
            anchors.leftMargin: control.height + UM.Theme.sizes.save_button_label_margin.width;

            color: UM.Theme.colors.save_button_text;
            font: UM.Theme.fonts.default;

            text: control.text;
        }
    }

    text: {
        if(base.progress < 0) {
            return qsTr("Please load a 3D model");
        } else if (base.progress < 0.95) {
            return qsTr("Calculating Print-time");
        } else {
            return qsTr("Estimated Print-time");
        }
    }

    onClicked: {
        if(Printer.outputDevice != "local_file") {
            Printer.writeToOutputDevice();
        } else if(base.saveAction) {
            base.saveAction.trigger();
        }
    }
}
