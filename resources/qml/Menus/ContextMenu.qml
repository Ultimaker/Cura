// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.1
import QtQuick.Window 2.1

import UM 1.5 as UM
import Cura 1.0 as Cura

Cura.Menu
{
    id: base

    property bool shouldShowExtruders: machineExtruderCount.properties.value > 1;

    property var multiBuildPlateModel: CuraApplication.getMultiBuildPlateModel()

    // Selection-related actions.
    Cura.MenuItem { action: Cura.Actions.centerSelection; }
    Cura.MenuItem { action: Cura.Actions.deleteSelection; }
    Cura.MenuItem { action: Cura.Actions.multiplySelection; }

    // Extruder selection - only visible if there is more than 1 extruder
    Cura.MenuSeparator { visible: base.shouldShowExtruders }
    Cura.MenuItem
    {
        id: extruderHeader
        text: catalog.i18ncp("@label", "Print Selected Model With:", "Print Selected Models With:", UM.Selection.selectionCount)
        enabled: false
        visible: base.shouldShowExtruders
    }

    Instantiator
    {
        model: CuraApplication.getExtrudersModel()
        Cura.MenuItem
        {
            text: "%1: %2 - %3".arg(model.name).arg(model.material).arg(model.variant)
            visible: base.shouldShowExtruders
            enabled: UM.Selection.hasSelection && model.enabled
            checkable: true
            checked: Cura.ExtruderManager.selectedObjectExtruders.indexOf(model.id) != -1
            onTriggered: CuraActions.setExtruderForSelection(model.id)
            shortcut: "Ctrl+" + (model.index + 1)
        }
        // Add it to the fifth position (and above) as we want it to be added after the extruder header.
        onObjectAdded: function(index, object) { base.insertItem(index + 5, object) }
        onObjectRemoved: function(object) {  base.removeItem(object) }
    }

    // Global actions
    Cura.MenuSeparator {}
    Cura.MenuItem { action: Cura.Actions.selectAll }
    Cura.MenuItem { action: Cura.Actions.arrangeAll }
    Cura.MenuItem { action: Cura.Actions.deleteAll }
    Cura.MenuItem { action: Cura.Actions.reloadAll }
    Cura.MenuItem { action: Cura.Actions.resetAllTranslation }
    Cura.MenuItem { action: Cura.Actions.resetAll }

    // Group actions
    Cura.MenuSeparator {}
    Cura.MenuItem { action: Cura.Actions.groupObjects }
    Cura.MenuItem { action: Cura.Actions.mergeObjects }
    Cura.MenuItem { action: Cura.Actions.unGroupObjects }

    Connections
    {
        target: UM.Controller
        function onContextMenuRequested() { base.popup() }
    }

    Connections
    {
        target: Cura.Actions.multiplySelection
        function onTriggered() { multiplyDialog.open() }
    }

    UM.SettingPropertyProvider
    {
        id: machineExtruderCount

        containerStack: Cura.MachineManager.activeMachine
        key: "machine_extruder_count"
        watchedProperties: [ "value" ]
    }

    UM.Dialog
    {
        id: multiplyDialog

        title: catalog.i18ncp("@title:window", "Multiply Selected Model", "Multiply Selected Models", UM.Selection.selectionCount)

        width: UM.Theme.getSize("small_popup_dialog").width
        height: UM.Theme.getSize("small_popup_dialog").height
        minimumWidth: UM.Theme.getSize("small_popup_dialog").width
        minimumHeight: UM.Theme.getSize("small_popup_dialog").height

        onAccepted: CuraActions.multiplySelection(copiesField.value)

        buttonSpacing: UM.Theme.getSize("thin_margin").width

        rightButtons:
        [
            Cura.SecondaryButton
            {
                text: "Cancel"
                onClicked: multiplyDialog.reject()
            },
            Cura.PrimaryButton
            {
                text: "Ok"
                onClicked: multiplyDialog.accept()
            }
        ]

        Row
        {
            spacing: UM.Theme.getSize("default_margin").width

            UM.Label
            {
                text: catalog.i18nc("@label", "Number of Copies")
                anchors.verticalCenter: copiesField.verticalCenter
                width: contentWidth
                wrapMode: Text.NoWrap
            }

            Cura.SpinBox
            {
                id: copiesField
                editable: true
                focus: true
                from: 1
                to: 99
                width: 2 * UM.Theme.getSize("button").width
            }
        }
    }
}
