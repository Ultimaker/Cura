// Copyright (c) 2018 Ultimaker B.V.
// PluginBrowser is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

// TODO: Switch to QtQuick.Controls 2.x and remove QtQuick.Controls.Styles

import UM 1.1 as UM

ScrollView
{
    anchors.fill: parent
    ListView
    {
        id: pluginList
        property var activePlugin
        property var filter: "installed"
        anchors
        {
            fill: parent
            topMargin: UM.Theme.getSize("default_margin").height
            bottomMargin: UM.Theme.getSize("default_margin").height
            leftMargin: UM.Theme.getSize("default_margin").width
            rightMargin: UM.Theme.getSize("default_margin").width
        }
        model: manager.pluginsModel
        delegate: PluginEntry {}
    }
}
