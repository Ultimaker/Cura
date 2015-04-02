import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Item {
    anchors.fill: parent;
    anchors.leftMargin: UM.Theme.sizes.default_margin.width;
    anchors.rightMargin: UM.Theme.sizes.default_margin.width;

    ColumnLayout {
        anchors.fill: parent;

        Item {
            Layout.fillWidth: true;
            Layout.preferredHeight: UM.Theme.sizes.section.height;

            Label {
                anchors.left: parent.left;
                anchors.verticalCenter: parent.verticalCenter;
                text: "00:00";
                font: UM.Theme.fonts.timeslider_time;
                color: UM.Theme.colors.primary;
            }
            Label { anchors.centerIn: parent; text: "Estimated Print Time"; color: UM.Theme.colors.text; }
            Label {
                anchors.right: parent.right;
                anchors.verticalCenter: parent.verticalCenter;
                text: "21:00";
                font: UM.Theme.fonts.timeslider_time;
                color: UM.Theme.colors.primary;
            }
        }

        Slider {
            Layout.fillWidth: true;
            Layout.preferredHeight: UM.Theme.sizes.section.height;

            minimumValue: 0;
            maximumValue: 100;

            style: SliderStyle {
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
                    color: UM.Theme.colors.slider_handle;
                }
            }
        }

        Item {
            Layout.fillWidth: true;
            Layout.preferredHeight: UM.Theme.sizes.section.height;

            Label {
                anchors.left: parent.left;
                anchors.verticalCenter: parent.verticalCenter;
                text: "Minimum\nDraft";
                color: UM.Theme.colors.text;
            }

            Label {
                anchors.right: parent.right;
                anchors.verticalCenter: parent.verticalCenter;
                text: "Maximum\nQuality";
                horizontalAlignment: Text.AlignRight;
                color: UM.Theme.colors.text;
            }
        }

        CheckBox {
            Layout.fillWidth: true;
            Layout.preferredHeight: UM.Theme.sizes.section.height;

            text: "Enable Support";

            style: CheckBoxStyle {
                background: Item { }
                indicator: Rectangle {
                    implicitWidth:  UM.Theme.sizes.checkbox.width;
                    implicitHeight: UM.Theme.sizes.checkbox.height;

                    color: control.hovered ? UM.Theme.colors.checkbox_hover : UM.Theme.colors.checkbox;
                    border.width: 1
                    border.color: UM.Theme.colors.checkbox_border;

                    Label {
                        anchors.centerIn: parent;
                        color: UM.Theme.colors.checkbox_mark;
//                         font: itemStyle.controlFont;

                        text: "✓";

                        opacity: control.checked ? 1 : 0;
                        Behavior on opacity { NumberAnimation { duration: 100; } }
                    }
                }
                label: Label {
                    text: control.text;
                    color: UM.Theme.colors.checkbox_text;
                }
            }
        }

        Item { Layout.fillWidth: true; Layout.fillHeight: true; }
    }
}
