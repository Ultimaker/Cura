// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.9
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.0 as Cura

UM.Dialog
{
    id: base
    title: catalog.i18nc("@title:window", "Save Project")

    minimumWidth: UM.Theme.getSize("popup_dialog").width
    minimumHeight: UM.Theme.getSize("popup_dialog").height
    width: minimumWidth
    height: minimumHeight

    backgroundColor: UM.Theme.getColor("main_background")

    property bool dontShowAgain: true

    function storeDontShowAgain()
    {
        UM.Preferences.setValue("cura/dialog_on_project_save", !dontShowAgainCheckbox.checked)
        UM.Preferences.setValue("cura/asked_dialog_on_project_save", true)
    }

    onClosing: storeDontShowAgain()
    onRejected: storeDontShowAgain()
    onAccepted: storeDontShowAgain()
    onVisibleChanged:
    {
        if(visible && UM.Preferences.getValue("cura/asked_dialog_on_project_save"))
        {
            dontShowAgain = !UM.Preferences.getValue("cura/dialog_on_project_save")
        }
    }

    Item
    {
        anchors.fill: parent

        UM.SettingDefinitionsModel
        {
            id: definitionsModel
            containerId: base.visible ? Cura.MachineManager.activeMachine != null ? Cura.MachineManager.activeMachine.definition.id: "" : ""
            showAll: true
            exclude: ["command_line_settings"]
            showAncestors: true
            expanded: ["*"]
            visibilityHandler: UM.SettingPreferenceVisibilityHandler { }
        }

        UM.Label
        {
            id: mainHeading
            width: parent.width
            text: catalog.i18nc("@action:title", "Summary - Cura Project")
            font.pointSize: 18
            anchors.top: parent.top
        }
        ScrollView
        {
            id: scroll
            width: parent.width
            anchors
            {
                top: mainHeading.bottom
                topMargin: UM.Theme.getSize("default_margin").height
                bottom: parent.bottom
                bottomMargin: UM.Theme.getSize("default_margin").height
            }

            ScrollBar.vertical: UM.ScrollBar
            {
                parent: scroll.parent
                anchors
                {
                    top: parent.top
                    right: parent.right
                    bottom: parent.bottom
                }
            }
            clip: true

            ColumnLayout
            {
                spacing: UM.Theme.getSize("default_margin").height
                Column
                {
                    UM.Label
                    {
                        id: settingsHeading
                        text: catalog.i18nc("@action:label", "Printer settings")
                        font.bold: true
                    }
                    Row
                    {
                        width: parent.width
                        height: childrenRect.height
                        UM.Label
                        {
                            text: catalog.i18nc("@action:label", "Type")
                            width: Math.floor(scroll.width / 3) | 0
                        }
                        UM.Label
                        {
                            text: Cura.MachineManager.activeMachine == null ? "" : Cura.MachineManager.activeMachine.definition.name
                            width: Math.floor(scroll.width / 3) | 0
                        }
                    }
                    Row
                    {
                        width: parent.width
                        height: childrenRect.height
                        UM.Label
                        {
                            text: Cura.MachineManager.activeMachineNetworkGroupName != "" ? catalog.i18nc("@action:label", "Printer Group") : catalog.i18nc("@action:label", "Name")
                            width: Math.floor(scroll.width / 3) | 0
                        }
                        UM.Label
                        {
                            text:
                            {
                                if(Cura.MachineManager.activeMachineNetworkGroupName != "")
                                {
                                    return Cura.MachineManager.activeMachineNetworkGroupName
                                }
                                if(Cura.MachineManager.activeMachine)
                                {
                                    return Cura.MachineManager.activeMachine.name
                                }
                                return ""
                            }
                            width: Math.floor(scroll.width / 3) | 0
                        }
                    }
                }
                Repeater
                {
                    width: parent.width
                    height: childrenRect.height
                    model: Cura.MachineManager.activeMachine ? Cura.MachineManager.activeMachine.extruderList : null
                    delegate: Column
                    {
                        height: childrenRect.height
                        width: parent.width
                        property string variantName:
                        {
                            var extruder = modelData
                            var variant_name = extruder.variant.name
                            return (variant_name !== undefined) ? variant_name : ""
                        }
                        property string materialName:
                        {
                            var extruder = modelData
                            var material_name = extruder.material.name
                            return (material_name !== undefined) ? material_name : ""
                        }
                        UM.Label
                        {
                            text: {
                                var extruder = Number(modelData.position)
                                var extruder_id = ""
                                if(!isNaN(extruder))
                                {
                                    extruder_id = extruder + 1 // The extruder counter start from One and not Zero
                                }
                                else
                                {
                                    extruder_id = modelData.position
                                }

                                return catalog.i18nc("@action:label", "Extruder %1").arg(extruder_id)
                            }
                            font.bold: true
                            enabled: modelData.isEnabled
                        }
                        Row
                        {
                            width: parent.width
                            height: childrenRect.height

                            UM.Label
                            {
                                text:
                                {
                                    if(variantName !== "" && materialName !== "")
                                    {
                                        return catalog.i18nc("@action:label", "%1 & material").arg(Cura.MachineManager.activeDefinitionVariantsName)
                                    }
                                    return catalog.i18nc("@action:label", "Material")
                                }
                                width: Math.floor(scroll.width / 3) | 0
                                enabled: modelData.isEnabled
                            }
                            UM.Label
                            {
                                text:
                                {
                                    if(variantName !== "" && materialName !== "")
                                    {
                                        return variantName + ", " + materialName
                                    }
                                    return materialName
                                }
                                enabled: modelData.isEnabled
                                width: Math.floor(scroll.width / 3) | 0
                            }
                        }
                    }
                }
                Column
                {
                    width: parent.width
                    height: childrenRect.height
                    UM.Label
                    {
                        text: catalog.i18nc("@action:label", "Profile settings")
                        font.bold: true
                    }
                    Row
                    {
                        width: parent.width
                        UM.Label
                        {
                            text: catalog.i18nc("@action:label", "Not in profile")
                            width: Math.floor(scroll.width / 3) | 0
                        }
                        UM.Label
                        {
                            text: catalog.i18ncp("@action:label", "%1 override", "%1 overrides", Cura.MachineManager.numUserSettings).arg(Cura.MachineManager.numUserSettings)
                            width: Math.floor(scroll.width / 3) | 0
                        }
                        visible: Cura.MachineManager.numUserSettings
                    }
                    Row
                    {
                        width: parent.width
                        height: childrenRect.height
                        UM.Label
                        {
                            text: catalog.i18nc("@action:label", "Name")
                            width: Math.floor(scroll.width / 3) | 0
                        }
                        UM.Label
                        {
                            text: Cura.MachineManager.activeQualityOrQualityChangesName
                            width: Math.floor(scroll.width / 3) | 0
                        }
                    }

                    // Intent
                    Row
                    {
                        width: parent.width
                        height: childrenRect.height
                        UM.Label
                        {
                            text: catalog.i18nc("@action:label", "Intent")
                            width: Math.floor(scroll.width / 3) | 0
                        }
                        UM.Label
                        {
                            text: Cura.MachineManager.activeIntentCategory
                            width: Math.floor(scroll.width / 3) | 0
                        }
                    }
                }
            }
        }
    }

    buttonSpacing: UM.Theme.getSize("thin_margin").width

    leftButtons:
    [
        UM.CheckBox
        {
            id: dontShowAgainCheckbox
            text: catalog.i18nc("@action:label", "Don't show project summary on save again")
            checked: dontShowAgain
        }
    ]

    rightButtons:
    [
        Cura.SecondaryButton
        {
            text: catalog.i18nc("@action:button", "Cancel")
            onClicked: base.reject()
        },
        Cura.PrimaryButton
        {
            text: catalog.i18nc("@action:button", "Save")
            onClicked: base.accept()
        }
    ]
}
