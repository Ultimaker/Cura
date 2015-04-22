import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Item {
    id: base;

    anchors.fill: parent;
    anchors.leftMargin: UM.Theme.sizes.default_margin.width;
    anchors.rightMargin: UM.Theme.sizes.default_margin.width;

    property Action configureSettings;

    property variant minimumPrintTime: PrintInformation.minimumPrintTime;
    property variant maximumPrintTime: PrintInformation.maximumPrintTime;

    ColumnLayout {
        anchors.fill: parent;

        Item {
            Layout.fillWidth: true;
            Layout.preferredHeight: UM.Theme.sizes.section.height;

            Label {
                anchors.left: parent.left;
                anchors.verticalCenter: parent.verticalCenter;
                text:Qt.formatTime(base.minimumPrintTime, "hh:mm");
                font: UM.Theme.fonts.timeslider_time;
                color: UM.Theme.colors.primary;
            }
            Label {
                anchors.centerIn: parent;
                text: {
                    if (UM.Backend.progress < 0)
                    {
                        return qsTr("No Model Loaded");
                    }
                    else if (base.minimumPrintTime == null || base.maximumPrintTime == null)
                    {
                        return qsTr("Calculating...")
                    }
                    else
                    {
                        return qsTr("Estimated Print Time");
                    }
                }
                color: UM.Theme.colors.text;
                font: UM.Theme.fonts.default;
            }
            Label {
                anchors.right: parent.right;
                anchors.verticalCenter: parent.verticalCenter;
                text: Qt.formatTime(base.maximumPrintTime, "hh:mm");
                font: UM.Theme.fonts.timeslider_time;
                color: UM.Theme.colors.primary;
            }
        }

        Slider {
            Layout.fillWidth: true;
            Layout.preferredHeight: UM.Theme.sizes.section.height;

            minimumValue: 0;
            maximumValue: 100;

            value: PrintInformation.timeQualityValue;
            onValueChanged: PrintInformation.setTimeQualityValue(value);

            style: UM.Theme.styles.slider;
        }

        Item {
            Layout.fillWidth: true;
            Layout.preferredHeight: UM.Theme.sizes.section.height;

            Label {
                anchors.left: parent.left;
                anchors.verticalCenter: parent.verticalCenter;
                text: "Minimum\nDraft";
                color: UM.Theme.colors.text;
                font: UM.Theme.fonts.default;
            }

            Label {
                anchors.right: parent.right;
                anchors.verticalCenter: parent.verticalCenter;
                text: "Maximum\nQuality";
                horizontalAlignment: Text.AlignRight;
                color: UM.Theme.colors.text;
                font: UM.Theme.fonts.default;
            }
        }

        CheckBox {
            Layout.fillWidth: true;
            Layout.preferredHeight: UM.Theme.sizes.section.height;

            text: "Enable Support";

            style: UM.Theme.styles.checkbox;
        }

        Item { Layout.fillWidth: true; Layout.fillHeight: true; }
    }
}
