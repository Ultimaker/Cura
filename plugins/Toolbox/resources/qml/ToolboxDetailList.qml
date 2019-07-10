// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    id: detailList
    ScrollView
    {
        frameVisible: false
        anchors.fill: detailList
        style: UM.Theme.styles.scrollview
        flickableItem.flickableDirection: Flickable.VerticalFlick
        Column
        {
            anchors
            {
                right: parent.right
                topMargin: UM.Theme.getSize("wide_margin").height
                bottomMargin: UM.Theme.getSize("wide_margin").height
                top: parent.top
            }
            height: childrenRect.height + 2 * UM.Theme.getSize("wide_margin").height
            spacing: UM.Theme.getSize("default_margin").height

            Repeater
            {
                model: toolbox.packagesModel
                delegate: Loader
                {
                    // FIXME: When using asynchronous loading, on Mac and Windows, the tile may fail to load complete,
                    // leaving an empty space below the title part. We turn it off for now to make it work on Mac and
                    // Windows.
                    // Can be related to this QT bug: https://bugreports.qt.io/browse/QTBUG-50992
                    asynchronous: false
                    source: "ToolboxDetailTile.qml"
                }
            }
        }
    }
}
