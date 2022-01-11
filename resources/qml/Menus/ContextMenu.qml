// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.1
import QtQuick.Dialogs 1.2
import QtQuick.Window 2.1

import UM 1.5 as UM
import Cura 1.0 as Cura

Menu
{
    id: base

    property bool shouldShowExtruders: machineExtruderCount.properties.value > 1;

    property var multiBuildPlateModel: CuraApplication.getMultiBuildPlateModel()

    // Selection-related actions.
    UM.MenuItem { action: Cura.Actions.centerSelection; }
    UM.MenuItem { action: Cura.Actions.deleteSelection; }
    UM.MenuItem { action: Cura.Actions.multiplySelection; }

    // Extruder selection - only visible if there is more than 1 extruder
    MenuSeparator { visible: base.shouldShowExtruders }
    UM.MenuItem
    {
        id: extruderHeader
        text: catalog.i18ncp("@label", "Print Selected Model With:", "Print Selected Models With:", UM.Selection.selectionCount)
        enabled: false
        visible: base.shouldShowExtruders
        height: visible ? implicitHeight: 0
    }

    Instantiator
    {
        model: CuraApplication.getExtrudersModel()
        UM.MenuItem
        {
            text: "%1: %2 - %3".arg(model.name).arg(model.material).arg(model.variant)
            visible: base.shouldShowExtruders
            height: visible ? implicitHeight: 0
            enabled: UM.Selection.hasSelection && model.enabled
            checkable: true
            checked: Cura.ExtruderManager.selectedObjectExtruders.indexOf(model.id) != -1
            onTriggered: CuraActions.setExtruderForSelection(model.id)
            shortcut: "Ctrl+" + (model.index + 1)
        }
        onObjectAdded: base.insertItem(index + 5, object)
        onObjectRemoved: base.removeItem(object)
    }

    // Global actions
    MenuSeparator {}
    UM.MenuItem { action: Cura.Actions.selectAll }
    UM.MenuItem { action: Cura.Actions.arrangeAll }
    UM.MenuItem { action: Cura.Actions.deleteAll }
    UM.MenuItem { action: Cura.Actions.reloadAll }
    UM.MenuItem { action: Cura.Actions.resetAllTranslation }
    UM.MenuItem { action: Cura.Actions.resetAll }

    // Group actions
    MenuSeparator {}
    UM.MenuItem { action: Cura.Actions.groupObjects }
    UM.MenuItem { action: Cura.Actions.mergeObjects }
    UM.MenuItem { action: Cura.Actions.unGroupObjects }

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

    Dialog
    {
        id: multiplyDialog
        modality: Qt.ApplicationModal

        title: catalog.i18ncp("@title:window", "Multiply Selected Model", "Multiply Selected Models", UM.Selection.selectionCount)


        onAccepted: CuraActions.multiplySelection(copiesField.value)

        signal reset()
        onReset:
        {
            copiesField.value = 1;
            copiesField.focus = true;
        }

        onVisibleChanged:
        {
            copiesField.forceActiveFocus();
        }

        standardButtons: StandardButton.Ok | StandardButton.Cancel

        Row
        {
            spacing: UM.Theme.getSize("default_margin").width

            Label
            {
                text: catalog.i18nc("@label", "Number of Copies")
                anchors.verticalCenter: copiesField.verticalCenter
            }

            SpinBox
            {
                id: copiesField
                focus: true
                from: 1
                to: 99
            }
        }
    }
}
