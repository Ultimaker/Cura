import QtQuick 2.3
import QtQuick.Controls 2.0
import UM 1.3 as UM

Rectangle {
    color: UM.Theme.getColor("monitor_tab_lining_inactive"); // TODO: Maybe theme separately? Maybe not.
    height: UM.Theme.getSize("default_lining").height;
    width: parent.width;
}