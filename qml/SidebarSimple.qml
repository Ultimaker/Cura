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

        RowLayout {
            Layout.fillWidth: true;

            Label { text: "00:00"; }
            Item { Layout.fillWidth: true; }
            Label { text: "Estimated Print Time"; }
            Item { Layout.fillWidth: true; }
            Label { text: "21:00"; }
        }

        Slider {
            Layout.fillWidth: true;

            style: SliderStyle { }
        }

        RowLayout {
            Layout.fillWidth: true;
            Label { text: "Minimum"; }
            Item { Layout.fillWidth: true; }
            Label { text: "Maximum"; }
        }

        CheckBox { text: "Auto Support"; style: CheckBoxStyle { } }

        Item { Layout.fillWidth: true; Layout.fillHeight: true; }
    }
}
