//Copyright (c) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import Qt.labs.qmlmodels 1.0
import QtQuick 2.1
import QtQuick.Controls 1.1 as OldControls
import QtQuick.Controls 2.15
import QtQuick.Dialogs 1.2
import QtQuick.Window 2.1

import UM 1.2 as UM
import Cura 1.6 as Cura

UM.Dialog
{
    id: base
    title: catalog.i18nc("@title:window", "Discard or Keep changes")

    minimumWidth: UM.Theme.getSize("popup_dialog").width
    minimumHeight: UM.Theme.getSize("popup_dialog").height
    width: minimumWidth
    height: minimumHeight
    property var changesModel: Cura.UserChangesModel{ id: userChangesModel}
    onVisibilityChanged:
    {
        if(visible)
        {
            changesModel.forceUpdate()

            discardOrKeepProfileChangesDropDownButton.currentIndex = 0;
            for (var i = 0; i < discardOrKeepProfileChangesDropDownButton.model.count; ++i)
            {
                var code = discardOrKeepProfileChangesDropDownButton.model.get(i).code;
                if (code == UM.Preferences.getValue("cura/choice_on_profile_override"))
                {
                    discardOrKeepProfileChangesDropDownButton.currentIndex = i;
                    break;
                }
            }
        }
    }

    Row
    {
        id: infoTextRow
        height: childrenRect.height
        anchors.margins: UM.Theme.getSize("default_margin").width
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        spacing: UM.Theme.getSize("default_margin").width

        UM.I18nCatalog
        {
            id: catalog;
            name: "cura"
        }

        Label
        {
            text: catalog.i18nc("@text:window, %1 is a profile name", "You have customized some profile settings.\nWould you like to Keep these changed settings after switching profiles?\nAlternatively, you can discard the changes to load the defaults from '%1'.").arg(Cura.MachineManager.activeQualityDisplayNameMap["main"])
            anchors.margins: UM.Theme.getSize("default_margin").width
            wrapMode: Text.WordWrap
        }
    }

    Item
    {
        anchors.margins: UM.Theme.getSize("default_margin").width
        anchors.top: infoTextRow.bottom
        anchors.bottom: optionRow.top
        anchors.left: parent.left
        anchors.right: parent.right

        Cura.TableView
        {
            id: tableView
            anchors
            {
                top: parent.top
                left: parent.left
                right: parent.right
            }
            height: base.height - 150

            columnHeaders: [
                catalog.i18nc("@title:column", "Profile settings"),
                Cura.MachineManager.activeQualityDisplayNameMap["main"],
                catalog.i18nc("@title:column", "Current changes")
            ]
            model: TableModel
            {
                TableModelColumn { display: "label" }
                TableModelColumn { display: "original_value" }
                TableModelColumn { display: "user_value" }
                rows: userChangesModel.items
            }
            sectionRole: "category"
        }
    }

    Item
    {
        id: optionRow
        anchors.bottom: buttonsRow.top
        anchors.right: parent.right
        anchors.left: parent.left
        anchors.margins: UM.Theme.getSize("default_margin").width
        height: childrenRect.height

        ComboBox
        {
            id: discardOrKeepProfileChangesDropDownButton
            width: 300
            textRole: "text"

            model: ListModel
            {
                id: discardOrKeepProfileListModel

                Component.onCompleted: {
                    append({ text: catalog.i18nc("@option:discardOrKeep", "Always ask me this"), code: "always_ask" })
                    append({ text: catalog.i18nc("@option:discardOrKeep", "Discard and never ask again"), code: "always_discard" })
                    append({ text: catalog.i18nc("@option:discardOrKeep", "Keep and never ask again"), code: "always_keep" })
                }
            }

            onActivated:
            {
                var code = model.get(index).code;
                UM.Preferences.setValue("cura/choice_on_profile_override", code);

                if (code == "always_keep") {
                    keepButton.enabled = true;
                    discardButton.enabled = false;
                }
                else if (code == "always_discard") {
                    keepButton.enabled = false;
                    discardButton.enabled = true;
                }
                else {
                    keepButton.enabled = true;
                    discardButton.enabled = true;
                }
            }
        }
    }

    Item
    {
        id: buttonsRow
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.left: parent.left
        anchors.margins: UM.Theme.getSize("default_margin").width
        height: childrenRect.height

        OldControls.Button
        {
            id: discardButton
            text: catalog.i18nc("@action:button", "Discard changes");
            anchors.right: parent.right
            onClicked:
            {
                CuraApplication.discardOrKeepProfileChangesClosed("discard")
                base.hide()
            }
            isDefault: true
        }

        OldControls.Button
        {
            id: keepButton
            text: catalog.i18nc("@action:button", "Keep changes");
            anchors.right: discardButton.left
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            onClicked:
            {
                CuraApplication.discardOrKeepProfileChangesClosed("keep")
                base.hide()
            }
        }
    }
}
