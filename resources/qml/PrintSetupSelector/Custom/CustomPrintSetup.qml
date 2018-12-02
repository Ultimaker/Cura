// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import Cura 1.0 as Cura


Item
{
    id: customPrintSetup

    // TODO: Hardcoded now but UX has to decide about the height of this item
    height: 500

    Cura.SettingView
    {
        anchors.fill: parent
    }
}
