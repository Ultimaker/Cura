// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

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

    onAboutToShow: extruderInstantiator.active = true
    onAboutToHide: extruderInstantiator.active = false
    Instantiator
    {
        id: extruderInstantiator
        model: activeMachine == null ? null : activeMachine.extruderList
        active: false
        asynchronous: true
        Menu
        {
            title: modelData.name

            NozzleMenu { title: Cura.MachineManager.activeDefinitionVariantsName; visible: Cura.MachineManager.hasVariants; extruderIndex: index }
            MaterialMenu { title: catalog.i18nc("@title:menu", "&Material"); visible: Cura.MachineManager.hasMaterials; extruderIndex: index }

            MenuSeparator
            {
                visible: Cura.MachineManager.hasVariants || Cura.MachineManager.hasMaterials
            }

            MenuItem
            {
                text: catalog.i18nc("@action:inmenu", "Set as Active Extruder")
                // HACK: Instead of directly binding to the onTriggered handle, we have to use this workaround.
                // I've narrowed it down to it being an issue with the instantiator (removing that makes the
                // onTriggered work directly again).
                Component.onCompleted:
                {
                    var index = model.index
                    triggered.connect(function(){Cura.ExtruderManager.setActiveExtruderIndex(index)})
                }
            }

            MenuItem
            {
                text: catalog.i18nc("@action:inmenu", "Enable Extruder")
                // HACK: Instead of directly binding to the onTriggered handle, we have to use this workaround.
                // I've narrowed it down to it being an issue with the instantiator (removing that makes the
                // onTriggered work directly again).
                Component.onCompleted:
                {
                    var index = model.index
                    triggered.connect(function(){Cura.MachineManager.setExtruderEnabled(index, true)})
                }
                visible: !Cura.MachineManager.getExtruder(model.index).isEnabled
            }

            MenuItem
            {
                text: catalog.i18nc("@action:inmenu", "Disable Extruder")
                // HACK: Instead of directly binding to the onTriggered handle, we have to use this workaround.
                // I've narrowed it down to it being an issue with the instantiator (removing that makes the
                // onTriggered work directly again).
                Component.onCompleted:
                {
                    var index = model.index
                    triggered.connect(function(){Cura.MachineManager.setExtruderEnabled(index, false)})
                }
                visible: Cura.MachineManager.getExtruder(model.index).isEnabled
                enabled: Cura.MachineManager.numberExtrudersEnabled > 1
            }

        }
        onObjectAdded: base.insertItem(index, object)
        onObjectRemoved: base.removeItem(object)
    }

    // TODO Only show in dev mode. Remove check when feature ready
    BuildplateMenu
    {
        title: catalog.i18nc("@title:menu", "&Build plate")
        visible: CuraSDKVersion == "dev" && Cura.MachineManager.hasVariantBuildplates
    }
    ProfileMenu { title: catalog.i18nc("@title:settings", "&Profile") }

    MenuSeparator { }

    MenuItem { action: Cura.Actions.configureSettingVisibility }
}