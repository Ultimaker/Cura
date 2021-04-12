

import QtQuick 2.7
import QtQuick.Controls 2.2
import QtQuick.Layouts 1.3

import UM 1.1 as UM

ScrollView {
    property alias model: pauseList.model
    width: parent.width
    clip: true
    ListView {
        id: pauseList
        width: parent.width
        delegate: Item
        {
            // Add a margin, otherwise the scrollbar is on top of the right most component
            width: parent.width - UM.Theme.getSize("default_margin").width
            height: childrenRect.height

            PauseListItem
            {
                id: pauseListItem
                width: parent.width
            }

            Rectangle {
                id: divider
                color: UM.Theme.getColor("lining")
                height: UM.Theme.getSize("default_lining").height
            }
        }
    }
}
