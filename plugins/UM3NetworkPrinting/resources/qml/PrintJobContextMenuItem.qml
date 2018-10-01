import QtQuick 2.2
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.4
import UM 1.3 as UM

Button {
    background: Rectangle {
        opacity: parent.down || parent.hovered ? 1 : 0;
        color: UM.Theme.getColor("viewport_background"); // TODO: Theme!
    }
    contentItem: Label {
        text: parent.text
        horizontalAlignment: Text.AlignLeft;
        verticalAlignment: Text.AlignVCenter;
    }
    height: 39 * screenScaleFactor; // TODO: Theme!
    hoverEnabled: true;
    visible: enabled;
    width: parent.width;
}