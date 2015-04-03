import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Item {
    anchors.fill: parent;
    anchors.leftMargin: UM.Theme.sizes.default_margin.width;
    anchors.rightMargin: UM.Theme.sizes.default_margin.width;

    property Action configureSettings;

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
            Label { anchors.centerIn: parent; text: "Estimated Print Time"; color: UM.Theme.colors.text; font: UM.Theme.fonts.default; }
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
