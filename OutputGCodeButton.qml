import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Button {
    id: saveButton;

    text: "Save";

    iconSource: UM.Resources.getIcon('save.png');

    onClicked: saveDialog.open();

    style: ButtonStyle {
        background: Rectangle {
            color: UM.Theme.primaryColor;
            border.width: 1;
            border.color: UM.Theme.borderColor;
        }
        label: Item {
            Label {
                anchors.verticalCenter: parent.verticalCenter;
                anchors.left: parent.left;
                anchors.right: icon.left;
                text: control.text;
                horizontalAlignment: Text.AlignHCenter;
                font.pointSize: UM.Theme.largeTextSize;
            }

            Rectangle {
                id: icon;

                anchors.right: parent.right;
                anchors.verticalCenter: parent.verticalCenter;

                width: control.height;
                height: control.height;
                UM.RecolorImage { anchors.centerIn: parent; source: control.iconSource; color: "#f00"; }
            }
        }
    }
}
