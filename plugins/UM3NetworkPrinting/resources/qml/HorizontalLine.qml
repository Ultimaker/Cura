import QtQuick 2.3
import QtQuick.Controls 2.0
import UM 1.3 as UM

Item {
    id: root;
    property var enabled: true;
    width: parent.width;
    height: childrenRect.height;

    Rectangle {
        anchors {
            left: parent.left;
            leftMargin: UM.Theme.getSize("default_margin").width;
            right: parent.right;
            rightMargin: UM.Theme.getSize("default_margin").width;
        }
        color: root.enabled ? UM.Theme.getColor("monitor_lining_inactive") : UM.Theme.getColor("monitor_lining_active");
        height: UM.Theme.getSize("default_lining").height;
    }
}