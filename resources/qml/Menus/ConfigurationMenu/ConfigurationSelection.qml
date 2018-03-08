// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: configurationSelector
    property var panelWidth: control.width
    property var panelVisible: false

    SyncButton { }

    Popup
    {
        id: popup
        y: configurationSelector.height - UM.Theme.getSize("default_lining").height
        x: configurationSelector.width - width
        width: panelWidth
        visible: panelVisible
        padding: UM.Theme.getSize("default_lining").width

        contentItem: ConfigurationListView {
            width: panelWidth - 2 * popup.padding
        }

        background: Rectangle {
            color: UM.Theme.getColor("setting_control")
            border.color: UM.Theme.getColor("setting_control_border")
        }
    }
}