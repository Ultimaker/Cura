// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

// TODO: Switch to QtQuick.Controls 2.x and remove QtQuick.Controls.Styles

import UM 1.1 as UM
import Cura 1.6 as Cura


UM.Dialog
{
    visible: true

    title: "Some title"
    minimumWidth: UM.Theme.getSize("license_window_minimum").width
    minimumHeight: UM.Theme.getSize("license_window_minimum").height
    width: minimumWidth
    height: minimumHeight

                ListView
                {
                    id: listView
                    anchors.fill: parent


                    model: toolbox.subscribedPackagesModel

                    delegate: Label
                    {
                        text: "A :)"
                    }
                }
}
