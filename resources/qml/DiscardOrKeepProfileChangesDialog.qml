// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Dialogs 1.2

import UM 1.2 as UM
import Cura 1.1 as Cura

UM.Dialog
{
    id: base
    title: catalog.i18nc("@title:window", "Discard or Keep changes")

    width: 500
    height: 300
    property var changesModel: Cura.UserChangesModel{ id: userChangesModel}
    onVisibilityChanged:
    {
        if(visible)
        {
            changesModel.forceUpdate()
        }
    }

    Column
    {
        anchors.fill: parent

        UM.I18nCatalog
        {
            id: catalog;
            name:"cura"
        }
        Label
        {
            text: "You have customized some default profile settings. Would you like to keep or discard those settings?"
            anchors.margins: UM.Theme.getSize("default_margin").width
            anchors.left: parent.left
            anchors.right: parent.right
            font: UM.Theme.getFont("default_bold")
            wrapMode: Text.WordWrap
        }
        Item // Spacer
        {
            height: UM.Theme.getSize("default_margin").height
            width: UM.Theme.getSize("default_margin").width
        }

        TableView
        {
            anchors.margins: UM.Theme.getSize("default_margin").width
            anchors.left: parent.left
            anchors.right: parent.right
            height: 200
            id: tableView
            Component
            {
                id: labelDelegate
                Label
                {
                    property var extruder_name: userChangesModel.getItem(styleData.row).extruder
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    font: UM.Theme.getFont("default")
                    text:
                    {
                        var result = styleData.value
                        if (extruder_name!= "")
                        {
                            result += " (" + extruder_name + ")"
                        }
                        return result
                    }
                }
            }

            Component
            {
                id: defaultDelegate
                Label
                {
                    text: styleData.value
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("setting_control_disabled_text")
                }
            }

            TableViewColumn
            {
                role: "label"
                title: catalog.i18nc("@title:column", "Profile settings")
                delegate: labelDelegate
                width: tableView.width * 0.5
            }

            TableViewColumn
            {
                role: "original_value"
                title: "default"
                width: tableView.width * 0.25
                delegate: defaultDelegate
            }
            TableViewColumn
            {
                role: "user_value"
                title: catalog.i18nc("@title:column", "Customized")
                width: tableView.width * 0.25 - 1
            }
            section.property: "category"
            section.delegate: Label
            {
                text: section
                font.bold: true
            }

            model: base.changesModel
        }

        Item // Spacer
        {
            height: UM.Theme.getSize("default_margin").height
            width: UM.Theme.getSize("default_margin").width
        }
        Row
        {
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            Button
            {
                text: catalog.i18nc("@action:button", "Keep");
                onClicked:
                {
                    Printer.discardOrKeepProfileChangesClosed("keep")
                    base.hide()
                }
            }
            Button
            {
                text: catalog.i18nc("@action:button", "Discard");
                onClicked:
                {
                    Printer.discardOrKeepProfileChangesClosed("discard")
                    base.hide()
                }
            }
        }
    }
}