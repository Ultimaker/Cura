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
        spacing: UM.Theme.getSize("default_margin").width

        UM.I18nCatalog
        {
            id: catalog;
            name:"cura"
        }

        Row
        {
            height: childrenRect.height
            anchors.margins: UM.Theme.getSize("default_margin").width
            anchors.left: parent.left
            anchors.right: parent.right
            spacing: UM.Theme.getSize("default_margin").width
            UM.RecolorImage
            {
                source: UM.Theme.getIcon("star")
                width : 30
                height: width
                color: UM.Theme.getColor("setting_control_button")
            }

            Label
            {
                text: "You have customized some profile settings.\nWould you like to keep or discard those settings?"
                anchors.margins: UM.Theme.getSize("default_margin").width
                font: UM.Theme.getFont("default_bold")
                wrapMode: Text.WordWrap
            }
        }

        TableView
        {
            anchors.margins: UM.Theme.getSize("default_margin").width
            anchors.left: parent.left
            anchors.right: parent.right
            height: base.height - 200
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
                title: "Default"
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

        Item
        {
            anchors.right: parent.right
            anchors.left: parent.left
            anchors.margins: UM.Theme.getSize("default_margin").width
            height:childrenRect.height

            ComboBox
            {
                id: discardOrKeepProfileChangesDropDownButton
                model: [
                    catalog.i18nc("@option:discardOrKeep", "Always ask me this"),
                    catalog.i18nc("@option:discardOrKeep", "Discard and never ask again"),
                    catalog.i18nc("@option:discardOrKeep", "Keep and never ask again")
                ]
                width: 300
                currentIndex: UM.Preferences.getValue("cura/choice_on_profile_override")
                onCurrentIndexChanged:
                {
                    UM.Preferences.setValue("cura/choice_on_profile_override", currentIndex)
                    if (currentIndex == 1) {
                        // 1 == "Discard and never ask again", so only enable the "Discard" button
                        discardButton.enabled = true
                        keepButton.enabled = false
                    }
                    else if (currentIndex == 2) {
                        // 2 == "Keep and never ask again", so only enable the "Keep" button
                        keepButton.enabled = true
                        discardButton.enabled = false
                    }
                    else {
                        // 0 == "Always ask me this", so show both
                        keepButton.enabled = true
                        discardButton.enabled = true
                    }
                }
            }
        }

        Item
        {
            anchors.right: parent.right
            anchors.left: parent.left
            anchors.margins: UM.Theme.getSize("default_margin").width
            height:childrenRect.height

            Button
            {
                id: discardButton
                text: catalog.i18nc("@action:button", "Discard");
                anchors.right: parent.right
                onClicked:
                {
                    Printer.discardOrKeepProfileChangesClosed("discard")
                    base.hide()
                }
                isDefault: true
            }

            Button
            {
                id: keepButton
                text: catalog.i18nc("@action:button", "Keep");
                anchors.right: discardButton.left
                anchors.rightMargin: UM.Theme.getSize("default_margin").width
                onClicked:
                {
                    Printer.discardOrKeepProfileChangesClosed("keep")
                    base.hide()
                }
            }

            Button
            {
                id: createNewProfileButton
                text: catalog.i18nc("@action:button", "Create New Profile");
                anchors.left: parent.left
                action: Cura.Actions.addProfile
                onClicked: base.hide()
            }
        }
    }
}