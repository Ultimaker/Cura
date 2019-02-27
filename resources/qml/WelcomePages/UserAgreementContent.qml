// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3


Component
{
    Column
    {
        spacing: 20

        Label
        {
            id: titleLabel
            anchors.horizontalCenter: parent.horizontalCenter
            horizontalAlignment: Text.AlignHCenter
            text: "User Agreement" // TODO
            color: "blue"  // TODO
            //font:
            renderType: NativeRendering
        }

        Image {
            id: curaImage
            anchors.horizontalCenter: parent.horizontalCenter
            source: "TODO"
        }

        Label
        {
            id: textLabel
            anchors.horizontalCenter: parent.horizontalCenter
            horizontalAlignment: Text.AlignHCenter
            text: "Please fllow these steps to set up\nUltimaker Cura. This will only take a few moments."
            //font:
            renderType: NativeRendering
        }
    }
}
