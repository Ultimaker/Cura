//Copyright (c) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.1 as Cura


//
// This component contains the content for the "Welcome" page of the welcome on-boarding process.
//
Cura.MachineAction
{
    id: base

    UM.I18nCatalog { id: catalog; name: "cura" }

    anchors.fill: parent

    property var extrudersModel: Cura.ExtrudersModel {}

    // Without a dialog (the first-start wizard) there are no buttons, the staged edits are written by the manager when
    // the user continues to the next page.
    readonly property bool hasDialog: !!base.dialog

    Component.onCompleted: manager.discardPendingChanges()
    Component.onDestruction:
    {
        if (manager)
        {
            manager.discardPendingChanges()
        }
    }

    // The dialog only handles the Return key by closing itself, which would lose the edits that the user is making.
    onDialogChanged:
    {
        if (base.dialog && base.dialog.closeOnAccept !== undefined)
        {
            base.dialog.closeOnAccept = false
        }
    }

    // Move the focus away from the field that is being edited, so that it commits what the user has typed.
    function commitActiveEdit()
    {
        saveButton.forceActiveFocus()
    }

    function closeDialog()
    {
        if (base.dialog)
        {
            base.dialog.visible = false
        }
    }

    // All settings edited in this action, found through the controls that are in draft mode.
    function shownSettings()
    {
        const result = []
        const queue = [tabStack]
        while (queue.length > 0)
        {
            const item = queue.pop()
            if (item.draftManager && item.settingKey)
            {
                result.push({ "stackId": item.containerStackId, "key": item.settingKey })
            }
            if (item.children)
            {
                for (let i = 0; i < item.children.length; i++)
                {
                    queue.push(item.children[i])
                }
            }
        }
        return result
    }

    function save()
    {
        commitActiveEdit()
        manager.applyPendingChanges()
        closeDialog()
    }

    function cancel()
    {
        manager.discardPendingChanges()
        closeDialog()
    }

    // Close the dialog, but ask what to do with the edits first if there are any that were not saved.
    function requestClose()
    {
        commitActiveEdit()
        if (manager.hasPendingChanges)
        {
            unsavedChangesDialogComponent.createObject(base).show()
        }
        else
        {
            closeDialog()
        }
    }

    Keys.onEscapePressed: function(event)
    {
        event.accepted = base.hasDialog
        if (base.hasDialog)
        {
            requestClose()
        }
    }

    Connections
    {
        target: base.dialog ? base.dialog : null
        ignoreUnknownSignals: true

        function onClosing(close)
        {
            base.commitActiveEdit()
            if (manager.hasPendingChanges)
            {
                close.accepted = false
                unsavedChangesDialogComponent.createObject(base).show()
            }
        }

        // The Escape key, when the focus was not inside of this action.
        function onRejected()
        {
            manager.discardPendingChanges()
        }
    }

    Component
    {
        id: unsavedChangesDialogComponent

        UM.Dialog
        {
            id: unsavedChangesDialog
            title: catalog.i18nc("@title:window", "Unsaved Changes")
            minimumWidth: UM.Theme.getSize("small_popup_dialog").width
            minimumHeight: UM.Theme.getSize("small_popup_dialog").height
            width: minimumWidth
            height: minimumHeight
            backgroundColor: UM.Theme.getColor("main_background")
            buttonSpacing: UM.Theme.getSize("default_margin").width

            selfDestroy: false
            onVisibleChanged:
            {
                if (!visible)
                {
                    destroy()
                }
            }

            UM.Label
            {
                anchors.left: parent.left
                anchors.right: parent.right
                text: catalog.i18nc("@info", "The machine settings have changed. Do you want to save these changes?")
                wrapMode: Text.WordWrap
            }

            leftButtons: [
                Cura.TertiaryButton
                {
                    text: catalog.i18nc("@action:button", "Discard Changes")
                    onClicked:
                    {
                        unsavedChangesDialog.visible = false
                        base.cancel()
                    }
                }
            ]

            rightButtons: [
                Cura.SecondaryButton
                {
                    text: catalog.i18nc("@action:button", "Keep Editing")
                    onClicked: unsavedChangesDialog.visible = false
                },
                Cura.PrimaryButton
                {
                    text: catalog.i18nc("@action:button", "Save")
                    onClicked:
                    {
                        unsavedChangesDialog.visible = false
                        base.save()
                    }
                }
            ]
        }
    }

    // If we create a TabButton for "Printer" and use Repeater for extruders, for some reason, once the component
    // finishes it will automatically change "currentIndex = 1", and it is VERY difficult to change "currentIndex = 0"
    // after that. Using a model and a Repeater to create both "Printer" and extruder TabButtons seem to solve this
    // problem.
    Connections
    {
        target: extrudersModel
        function onItemsChanged() { tabNameModel.update() }
    }

    ListModel
    {
        id: tabNameModel

        Component.onCompleted: update()

        function update()
        {
            clear()
            append({ name: catalog.i18nc("@title:tab", "Printer") })
            for (var i = 0; i < extrudersModel.count; i++)
            {
                const m = extrudersModel.getItem(i)
                append({ name: m.name })
            }
        }
    }

    Cura.RoundedRectangle
    {
        anchors
        {
            top: tabBar.bottom
            topMargin: -UM.Theme.getSize("default_lining").height
            bottom: buttonBar.top
            left: parent.left
            right: parent.right
        }
        cornerSide: Cura.RoundedRectangle.Direction.Down
        border.color: UM.Theme.getColor("lining")
        border.width: UM.Theme.getSize("default_lining").width
        radius: UM.Theme.getSize("default_radius").width
        color: UM.Theme.getColor("main_background")
        StackLayout
        {
            id: tabStack
            anchors.fill: parent

            currentIndex: tabBar.currentIndex

            MachineSettingsPrinterTab
            {
                id: printerTab
            }

            Repeater
            {
                model: extrudersModel
                delegate: MachineSettingsExtruderTab
                {
                    id: discoverTab
                    extruderPosition: model.index
                    extruderStackId: model.id
                }
            }
        }
    }

    Item  // Save / Cancel / Restore Defaults
    {
        id: buttonBar
        visible: base.hasDialog
        anchors
        {
            left: parent.left
            right: parent.right
            bottom: parent.bottom
        }
        height: visible ? saveButton.height + UM.Theme.getSize("default_margin").height : 0

        Cura.SecondaryButton
        {
            id: restoreDefaultsButton
            anchors.left: parent.left
            anchors.bottom: parent.bottom
            text: catalog.i18nc("@action:button", "Restore Defaults")
            onClicked:
            {
                base.commitActiveEdit()
                manager.restoreDefaults(base.shownSettings())
            }
        }

        Row
        {
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            spacing: UM.Theme.getSize("default_margin").width

            Cura.SecondaryButton
            {
                id: cancelButton
                text: catalog.i18nc("@action:button", "Cancel")
                onClicked: base.cancel()
            }

            Cura.PrimaryButton
            {
                id: saveButton
                text: catalog.i18nc("@action:button", "Save")
                onClicked: base.save()
            }
        }
    }

    UM.Label
    {
        id: machineNameLabel
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        text: Cura.MachineManager.activeMachine.name
        horizontalAlignment: Text.AlignHCenter
        font: UM.Theme.getFont("large_bold")
    }

    UM.TabRow
    {
        id: tabBar
        anchors.top: machineNameLabel.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: parent.width
        Repeater
        {
            model: tabNameModel
            delegate: UM.TabRowButton
            {
                checked: model.index == 0
                text: model.name
            }
        }
    }
}
