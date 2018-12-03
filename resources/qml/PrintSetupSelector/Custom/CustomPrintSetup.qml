// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.3 as UM
import Cura 1.0 as Cura


Item
{
    id: customPrintSetup

    // TODO: Hardcoded now but UX has to decide about the height of this item
    height: 500

    property real padding: UM.Theme.getSize("default_margin").width

    // Profile selector row
    GlobalProfileSelector
    {
        id: globalProfileRow
        anchors
        {
            top: parent.top
            topMargin: parent.padding
            left: parent.left
            leftMargin: parent.padding
            right: parent.right
            rightMargin: parent.padding
        }
    }

    Cura.SettingView
    {
        anchors
        {
            top: globalProfileRow.bottom
            topMargin: UM.Theme.getSize("default_margin").height
            left: parent.left
            leftMargin: parent.padding
            right: parent.right
            rightMargin: parent.padding
            bottom: parent.bottom
        }
    }
}
