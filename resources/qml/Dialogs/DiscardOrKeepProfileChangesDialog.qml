//Copyright (c) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import Qt.labs.qmlmodels 1.0
import QtQuick 2.1
import QtQuick.Controls 2.15

import UM 1.5 as UM
import Cura 1.6 as Cura

UM.Dialog
{
    id: base
    title: catalog.i18nc("@title:window", "Discard or Keep changes")

    onAccepted: CuraApplication.discardOrKeepProfileChangesClosed("discard")
    onRejected: CuraApplication.discardOrKeepProfileChangesClosed("keep")

    minimumWidth: UM.Theme.getSize("popup_dialog").width
    minimumHeight: UM.Theme.getSize("popup_dialog").height
    width: minimumWidth
    height: minimumHeight

    margin: UM.Theme.getSize("thick_margin").width

    property var changesModel: Cura.UserChangesModel { id: userChangesModel }

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

    UM.Label
    {
        id: infoText
        text: catalog.i18nc("@text:window, %1 is a profile name", "You have customized some profile settings. Would you like to Keep these changed settings after switching profiles? Alternatively, you can discard the changes to load the defaults from '%1'.").arg(Cura.MachineManager.activeQualityDisplayNameMap["main"])
        anchors.left: parent.left
        anchors.right: parent.right
        wrapMode: Text.WordWrap

        UM.I18nCatalog
        {
            id: catalog
            name: "cura"
        }
    }

    Item
    {
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.top: infoText.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right

        Cura.TableView
        {
            id: tableView
            anchors.fill: parent

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

    buttonSpacing: UM.Theme.getSize("thin_margin").width

    leftButtons: [
        Cura.ComboBox
        {
            implicitHeight: UM.Theme.getSize("combobox_dialog").height
            implicitWidth: UM.Theme.getSize("combobox_dialog").width

            id: discardOrKeepProfileChangesDropDownButton
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
    ]

    rightButtons:
    [
        Cura.PrimaryButton
        {
            id: discardButton
            text: catalog.i18nc("@action:button", "Discard changes")
            onClicked: base.accept()
        },
        Cura.SecondaryButton
        {
            id: keepButton
            text: catalog.i18nc("@action:button", "Keep changes")
            onClicked: base.reject()
        }
    ]
}
