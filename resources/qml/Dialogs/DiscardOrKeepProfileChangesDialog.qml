//Copyright (c) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 2.15

import UM 1.6 as UM
import Cura 1.6 as Cura

UM.Dialog
{
    id: base
    title: catalog.i18nc("@title:window", "Discard or Keep changes")

    enum ButtonsType { DiscardOrKeep, SaveFromBuiltIn, SaveFromCustom}
    property int buttonState: DiscardOrKeepProfileChangesDialog.ButtonsType.DiscardOrKeep

    onAccepted: buttonState == DiscardOrKeepProfileChangesDialog.ButtonsType.DiscardOrKeep ?
        CuraApplication.discardOrKeepProfileChangesClosed("discard") : Cura.Actions.addProfile.trigger()
    onRejected: buttonState == DiscardOrKeepProfileChangesDialog.ButtonsType.DiscardOrKeep ?
        CuraApplication.discardOrKeepProfileChangesClosed("keep") : Cura.Actions.updateProfile.trigger()

    minimumWidth: UM.Theme.getSize("popup_dialog").width
    minimumHeight: UM.Theme.getSize("popup_dialog").height
    width: minimumWidth
    height: minimumHeight
    backgroundColor: UM.Theme.getColor("background_1")
    margin: UM.Theme.getSize("thick_margin").width

    property var changesModel: Cura.UserChangesModel { id: userChangesModel }

    // Hack to make sure that when the data of our model changes the tablemodel is also updated
    // If we directly set the rows (So without the clear being called) it doesn't seem to
    // get updated correctly.
    property var modelRows: userChangesModel.items
    onModelRowsChanged:
    {
        tableModel.clear()
        tableModel.rows = modelRows
    }

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
        text: catalog.i18nc("@text:window, %1 is a profile name", "You have customized some profile settings. Would you like to Keep these changed settings after switching profiles? Alternatively, you can discard the changes to load the defaults from '%1'.").arg(Cura.MachineManager.activeQualityDisplayNameMainStringParts.join(" - "))
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
                Cura.MachineManager.activeQualityDisplayNameMainStringParts.join(" - "),
                catalog.i18nc("@title:column", "Current changes")
            ]
            model: UM.TableModel
            {
                id: tableModel
                headers: ["label", "original_value", "user_value"]
                rows: modelRows
            }
            sectionRole: "category"
        }
    }

    buttonSpacing: UM.Theme.getSize("thin_margin").width

    leftButtons:
    [
        Cura.ComboBox
        {
            visible: buttonState === DiscardOrKeepProfileChangesDialog.ButtonsType.DiscardOrKeep

            implicitHeight: UM.Theme.getSize("combobox").height
            implicitWidth: UM.Theme.getSize("combobox").width

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
                const code = model.get(index).code;
                UM.Preferences.setValue("cura/choice_on_profile_override", code);

                switch (code) {
                    case "always_keep":
                        keepButton.enabled = true;
                        discardButton.enabled = false;
                        break;
                    case "always_discard":
                        keepButton.enabled = false;
                        discardButton.enabled = true;
                        break;
                    default:
                        keepButton.enabled = true;
                        discardButton.enabled = true;
                        break;
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
            visible: buttonState == DiscardOrKeepProfileChangesDialog.ButtonsType.DiscardOrKeep
        },
        Cura.SecondaryButton
        {
            id: keepButton
            text: catalog.i18nc("@action:button", "Keep changes")
            onClicked: base.reject()
            visible: buttonState == DiscardOrKeepProfileChangesDialog.ButtonsType.DiscardOrKeep
        },
        Cura.SecondaryButton
        {
            id: overwriteButton
            text: catalog.i18nc("@action:button", "Save as new custom profile")
            visible: buttonState != DiscardOrKeepProfileChangesDialog.ButtonsType.DiscardOrKeep
            onClicked: base.accept()
        },
        Cura.PrimaryButton
        {
            id: saveButton
            text: catalog.i18nc("@action:button", "Save changes")
            visible: buttonState == DiscardOrKeepProfileChangesDialog.ButtonsType.SaveFromCustom
            onClicked: base.reject()
        }
    ]
}
