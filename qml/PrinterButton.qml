import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Button {
    id: base;
    style: UM.Theme.styles.tool_button;

    Rectangle {
        anchors.bottom: parent.top;

        width: parent.width;
        height: base.hovered ? label.height : 0;
        Behavior on height { NumberAnimation { duration: 75; } }

        opacity: base.hovered ? 1.0 : 0.0;
        Behavior on opacity { NumberAnimation { duration: 75; } }

        Label {
            id: label
            anchors.horizontalCenter: parent.horizontalCenter;
            text: base.text;
            font: UM.Theme.fonts.button_tooltip;
        }
    }
}
