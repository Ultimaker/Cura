import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

UM.AngledCornerRectangle {
    id: base;

    property Action addMachineAction;
    property Action configureMachinesAction;

    cornerSize: UM.Theme.sizes.default_margin.width;

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons;

        onWheel: {
            wheel.accepted = true;
        }
    }

    ColumnLayout {
        anchors.fill: parent;
        anchors.topMargin: UM.Theme.sizes.default_margin.height;
        anchors.bottomMargin: UM.Theme.sizes.default_margin.height;

        spacing: UM.Theme.sizes.default_margin.height;

        SidebarHeader {
            id: header;

            Layout.fillWidth: true;

            addMachineAction: base.addMachineAction;
            configureMachinesAction: base.configureMachinesAction;
        }

        Loader {
            id: sidebarContents;

            Layout.fillWidth: true;
            Layout.fillHeight: true;

            source: header.currentModeFile;
        }

        OutputGCodeButton {
            Layout.preferredWidth: base.width - UM.Theme.sizes.default_margin.width * 2;
            Layout.preferredHeight: UM.Theme.sizes.button.height;
            Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter;
        }
    }
}
