//Copyright (c) 2020 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: base
    title: catalog.i18nc("@title:menu menubar:toplevel", "&Settings")

    PrinterMenu { title: catalog.i18nc("@title:menu menubar:settings", "&Printer") }

    property var activeMachine: Cura.MachineManager.activeMachine
    Instantiator
    {
        id: extruderInstantiator
        model: activeMachine == null ? null : activeMachine.extruderList
        Menu
        {
            title: modelData.name
            property var extruder: (base.activeMachine === null) ? null : activeMachine.extruderList[model.index]
            NozzleMenu { title: Cura.MachineManager.activeDefinitionVariantsName; visible: Cura.MachineManager.activeMachine.hasVariants; extruderIndex: index }
            MaterialMenu { title: catalog.i18nc("@title:menu", "&Material"); visible: Cura.MachineManager.activeMachine.hasMaterials; extruderIndex: index }

            MenuSeparator
            {
                visible: Cura.MachineManager.activeMachine.hasVariants || Cura.MachineManager.activeMachine.hasMaterials
            }

            MenuItem
            {
                text: catalog.i18nc("@action:inmenu", "Set as Active Extruder")
                onTriggered: Cura.ExtruderManager.setActiveExtruderIndex(model.index)
            }

            MenuItem
            {
                text: catalog.i18nc("@action:inmenu", "Enable Extruder")
                onTriggered: Cura.MachineManager.setExtruderEnabled(model.index, true)
                visible: (extruder === null || extruder === undefined) ? false : !extruder.isEnabled
            }

            MenuItem
            {
                text: catalog.i18nc("@action:inmenu", "Disable Extruder")
                onTriggered: Cura.MachineManager.setExtruderEnabled(index, false)
                visible: (extruder === null || extruder === undefined) ? false : extruder.isEnabled
                enabled: Cura.MachineManager.numberExtrudersEnabled > 1
            }

        }
        onObjectAdded: base.insertItem(index, object)
        onObjectRemoved: base.removeItem(object)
    }

    MenuSeparator { }

    MenuItem { action: Cura.Actions.configureSettingVisibility }
}