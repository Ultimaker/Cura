// Copyright (c) 2020 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtQuick.Window 2.2

import UM 1.5 as UM
import Cura 1.1 as Cura

UM.Dialog
{
    id: workspaceDialog
    title: catalog.i18nc("@title:window", "Open Project")

    minimumWidth: UM.Theme.getSize("modal_window_minimum").width
    minimumHeight: UM.Theme.getSize("modal_window_minimum").height
    width: minimumWidth
    height: minimumHeight

    backgroundColor: UM.Theme.getColor("main_background")
    margin: UM.Theme.getSize("default_margin").width
    property int comboboxHeight: UM.Theme.getSize("default_margin").height

    onClosing: manager.notifyClosed()
    onVisibleChanged:
    {
        if (visible)
        {
            machineResolveComboBox.currentIndex = 0
            qualityChangesResolveComboBox.currentIndex = 0
            materialResolveComboBox.currentIndex = 0
        }
    }

    Flickable
    {
        clip: true
        width: parent.width
        height: parent.height
        contentHeight: dialogSummaryItem.height
        ScrollBar.vertical: UM.ScrollBar { id: verticalScrollBar }

        Item
        {
            id: dialogSummaryItem
            width: verticalScrollBar.visible ? parent.width - verticalScrollBar.width - UM.Theme.getSize("default_margin").width : parent.width
            height: childrenRect.height
            anchors.margins: 10 * screenScaleFactor

            UM.I18nCatalog
            {
                id: catalog
                name: "cura"
            }

            ListModel
            {
                id: resolveStrategiesModel
                // Instead of directly adding the list elements, we add them afterwards.
                // This is because it's impossible to use setting function results to be bound to listElement properties directly.
                // See http://stackoverflow.com/questions/7659442/listelement-fields-as-properties
                Component.onCompleted:
                {
                    append({"key": "override", "label": catalog.i18nc("@action:ComboBox Update/override existing profile", "Update existing")});
                    append({"key": "new", "label": catalog.i18nc("@action:ComboBox Save settings in a new profile", "Create new")});
                }
            }

            Column
            {
                width: parent.width
                height: childrenRect.height
                spacing: UM.Theme.getSize("default_margin").height

                Column
                {
                    width: parent.width
                    height: childrenRect.height
                    spacing: UM.Theme.getSize("default_margin").height

                    UM.Label
                    {
                        id: titleLabel
                        anchors.margins: UM.Theme.getSize("default_margin").height
                        text: catalog.i18nc("@action:title", "Summary - Cura Project")
                        font: UM.Theme.getFont("large")
                    }
                }

                Item
                {
                    width: parent.width
                    height: childrenRect.height
                    anchors.leftMargin: UM.Theme.getSize("default_margin")

                    UM.TooltipArea
                    {
                        id: machineResolveStrategyTooltip
                        anchors.top: parent.top
                        anchors.right: parent.right
                        width: (parent.width / 3) | 0
                        height: visible ? comboboxHeight : 0
                        visible: workspaceDialog.visible && machineResolveComboBox.model.count > 1
                        text: catalog.i18nc("@info:tooltip", "How should the conflict in the machine be resolved?")

                        UM.Label
                        {
                            id: open_with_label
                            anchors.top: parent.top
                            anchors.left: parent.left
                            anchors.bottomMargin: UM.Theme.getSize("default_margin").height
                            text: catalog.i18nc("@action:label", "Open With")
                            font: UM.Theme.getFont("default_bold")
                        }

                        Cura.ComboBox
                        {
                            id: machineResolveComboBox
                            anchors.top: open_with_label.bottom
                            anchors.left: parent.left
                            model: manager.updatableMachinesModel
                            visible: machineResolveStrategyTooltip.visible
                            textRole: "displayName"
                            width: parent.width
                            height: UM.Theme.getSize("button").height
                            onCurrentIndexChanged:
                            {
                                if (model.getItem(currentIndex).id == "new"
                                    && model.getItem(currentIndex).type == "default_option")
                                {
                                    manager.setResolveStrategy("machine", "new")
                                }
                                else
                                {
                                    manager.setResolveStrategy("machine", "override")
                                    manager.setMachineToOverride(model.getItem(currentIndex).id)
                                }
                            }

                            onVisibleChanged:
                            {
                                if (!visible) {return}

                                currentIndex = 0
                                // If the project printer exists in Cura, set it as the default dropdown menu option.
                                // No need to check object 0, which is the "Create new" option
                                for (var i = 1; i < model.count; i++)
                                {
                                    if (model.getItem(i).name == manager.machineName)
                                    {
                                        currentIndex = i
                                        break
                                    }
                                }
                                // The project printer does not exist in Cura. If there is at least one printer of the same
                                // type, select the first one, else set the index to "Create new"
                                if (currentIndex == 0 && model.count > 1)
                                {
                                    currentIndex = 1
                                }
                            }
                        }
                    }

                    Row
                    {
                        id: printerSettingsTitleRow
                        anchors.top: parent.top
                        anchors.bottomMargin: UM.Theme.getSize("default_margin").height
                        spacing: UM.Theme.getSize("default_margin").width

                        UM.ColorImage
                        {
                            anchors.verticalCenter: parent.verticalCenter
                            source: UM.Theme.getIcon("Printer")
                            height: UM.Theme.getSize("medium_button_icon").height
                            width: height
                        }
                        UM.Label
                        {
                            text: catalog.i18nc("@action:label", "Printer settings")
                            anchors.verticalCenter: parent.verticalCenter
                            font: UM.Theme.getFont("default_bold")
                        }
                    }

                    Column
                    {
                        id: printerSettingsValuesTable
                        width: parent.width
                        height: childrenRect.height
                        spacing: UM.Theme.getSize("default_margin").height
                        leftPadding: UM.Theme.getSize("medium_button_icon").width + UM.Theme.getSize("default_margin").width
                        anchors.top: printerSettingsTitleRow.bottom

                        Row
                        {
                            width: parent.width
                            height: childrenRect.height

                            UM.Label
                            {
                                text: catalog.i18nc("@action:label", "Type")
                                width: (parent.width / 3) | 0
                            }
                            UM.Label
                            {
                                text: manager.machineType
                                width: (parent.width / 3) | 0
                            }
                        }

                        Row
                        {
                            width: parent.width
                            height: childrenRect.height

                            UM.Label
                            {
                                text: catalog.i18nc("@action:label", manager.isPrinterGroup ? "Printer Group" : "Printer Name")
                                width: (parent.width / 3) | 0
                            }
                            UM.Label
                            {
                                text: manager.machineName
                                width: (parent.width / 3) | 0
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                }

                Item
                {
                    width: parent.width
                    height: childrenRect.height

                    UM.TooltipArea
                    {
                        anchors.right: parent.right
                        anchors.top: parent.top
                        width: (parent.width / 3) | 0
                        height: visible ? comboboxHeight : 0
                        visible: manager.qualityChangesConflict
                        text: catalog.i18nc("@info:tooltip", "How should the conflict in the profile be resolved?")
                        Cura.ComboBox
                        {
                            model: resolveStrategiesModel
                            textRole: "label"
                            id: qualityChangesResolveComboBox
                            width: parent.width
                            height: UM.Theme.getSize("button").height
                            onActivated:
                            {
                                manager.setResolveStrategy("quality_changes", resolveStrategiesModel.get(index).key)
                            }
                        }
                    }

                    Row
                    {
                        id: profileSettingsTitleRow
                        anchors.top: parent.top
                        anchors.bottomMargin: UM.Theme.getSize("default_margin").height
                        spacing: UM.Theme.getSize("default_margin").width

                        UM.ColorImage
                        {
                            anchors.verticalCenter: parent.verticalCenter
                            source: UM.Theme.getIcon("Printer")
                            height: UM.Theme.getSize("medium_button_icon").height
                            width: height
                        }
                        UM.Label
                        {
                            text: catalog.i18nc("@action:label", "Profile settings")
                            anchors.verticalCenter: parent.verticalCenter
                            font: UM.Theme.getFont("default_bold")
                        }
                    }

                    Column
                    {
                        id: profileSettingsValuesTable
                        width: parent.width
                        height: childrenRect.height
                        spacing: UM.Theme.getSize("default_margin").height
                        leftPadding: UM.Theme.getSize("medium_button_icon").width + UM.Theme.getSize("default_margin").width
                        anchors.top: profileSettingsTitleRow.bottom

                        Row
                        {
                            width: parent.width
                            height: childrenRect.height

                            UM.Label
                            {
                                text: catalog.i18nc("@action:label", "Name")
                                width: (parent.width / 3) | 0
                            }
                            UM.Label
                            {
                                text: manager.qualityName
                                width: (parent.width / 3) | 0
                                wrapMode: Text.WordWrap
                            }
                        }

                        Row
                        {
                            width: parent.width
                            height: childrenRect.height

                            UM.Label
                            {
                                text: catalog.i18nc("@action:label", "Intent")
                                width: (parent.width / 3) | 0
                            }
                            UM.Label
                            {
                                text: manager.intentName
                                width: (parent.width / 3) | 0
                                wrapMode: Text.WordWrap
                            }
                        }

                        Row
                        {
                            width: parent.width
                            height: childrenRect.height

                            UM.Label
                            {
                                text: catalog.i18nc("@action:label", "Not in profile")
                                visible: manager.numUserSettings != 0
                                width: (parent.width / 3) | 0
                            }
                            UM.Label
                            {
                                text: catalog.i18ncp("@action:label", "%1 override", "%1 overrides", manager.numUserSettings).arg(manager.numUserSettings)
                                visible: manager.numUserSettings != 0
                                width: (parent.width / 3) | 0
                            }
                        }

                        Row
                        {
                            width: parent.width
                            height: childrenRect.height

                            UM.Label
                            {
                                text: catalog.i18nc("@action:label", "Derivative from")
                                visible: manager.numSettingsOverridenByQualityChanges != 0
                                width: (parent.width / 3) | 0
                            }
                            UM.Label
                            {
                                text: catalog.i18ncp("@action:label", "%1, %2 override", "%1, %2 overrides", manager.numSettingsOverridenByQualityChanges).arg(manager.qualityType).arg(manager.numSettingsOverridenByQualityChanges)
                                width: (parent.width / 3) | 0
                                visible: manager.numSettingsOverridenByQualityChanges != 0
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                }

                Item
                {
                    width: parent.width
                    height: childrenRect.height

                    UM.TooltipArea
                    {
                        id: materialResolveTooltip
                        anchors.right: parent.right
                        anchors.top: parent.top
                        width: (parent.width / 3) | 0
                        height: visible ? comboboxHeight : 0
                        visible: manager.materialConflict
                        text: catalog.i18nc("@info:tooltip", "How should the conflict in the material be resolved?")
                        Cura.ComboBox
                        {
                            model: resolveStrategiesModel
                            textRole: "label"
                            id: materialResolveComboBox
                            width: parent.width
                            height: UM.Theme.getSize("button").height
                            onActivated:
                            {
                                manager.setResolveStrategy("material", resolveStrategiesModel.get(index).key)
                            }
                        }
                    }

                    Row
                    {
                        id: materialSettingsTitleRow
                        anchors.top: parent.top
                        anchors.bottomMargin: UM.Theme.getSize("default_margin").height
                        spacing: UM.Theme.getSize("default_margin").width

                        UM.ColorImage
                        {
                            anchors.verticalCenter: parent.verticalCenter
                            source: UM.Theme.getIcon("Printer")
                            height: UM.Theme.getSize("medium_button_icon").height
                            width: height
                        }
                        UM.Label
                        {
                            text: catalog.i18nc("@action:label", "Material settings")
                            anchors.verticalCenter: parent.verticalCenter
                            font: UM.Theme.getFont("default_bold")
                        }
                    }

                    Column
                    {
                        width: parent.width
                        height: childrenRect.height
                        spacing: UM.Theme.getSize("default_margin").height
                        leftPadding: UM.Theme.getSize("medium_button_icon").width + UM.Theme.getSize("default_margin").width
                        anchors.top: materialSettingsTitleRow.bottom

                        Repeater
                        {
                            model: manager.materialLabels
                            delegate: Row
                            {
                                width: parent.width
                                height: childrenRect.height
                                UM.Label
                                {
                                    text: catalog.i18nc("@action:label", "Name")
                                    width: (parent.width / 3) | 0
                                }
                                UM.Label
                                {
                                    text: modelData
                                    width: (parent.width / 3) | 0
                                    wrapMode: Text.WordWrap
                                }
                            }
                        }
                    }
                }

                Item
                {
                    width: parent.width
                    height: childrenRect.height

                    Row
                    {
                        id: visibilitySettingsTitleRow
                        anchors.top: parent.top
                        anchors.bottomMargin: UM.Theme.getSize("default_margin").height
                        spacing: UM.Theme.getSize("default_margin").width

                        UM.ColorImage
                        {
                            anchors.verticalCenter: parent.verticalCenter
                            source: UM.Theme.getIcon("Printer")
                            height: UM.Theme.getSize("medium_button_icon").height
                            width: height
                        }
                        UM.Label
                        {
                            text: catalog.i18nc("@action:label", "Setting visibility")
                            anchors.verticalCenter: parent.verticalCenter
                            font: UM.Theme.getFont("default_bold")
                        }
                    }

                    Column
                    {
                        width: parent.width
                        height: childrenRect.height
                        spacing: UM.Theme.getSize("default_margin").height
                        leftPadding: UM.Theme.getSize("medium_button_icon").width + UM.Theme.getSize("default_margin").width
                        anchors.top: visibilitySettingsTitleRow.bottom

                        Row
                        {
                            width: parent.width
                            height: childrenRect.height
                            UM.Label
                            {
                                text: catalog.i18nc("@action:label", "Mode")
                                width: (parent.width / 3) | 0
                            }
                            UM.Label
                            {
                                text: manager.activeMode
                                width: (parent.width / 3) | 0
                            }
                        }
                        Row
                        {
                            width: parent.width
                            height: childrenRect.height
                            visible: manager.hasVisibleSettingsField
                            UM.Label
                            {
                                text: catalog.i18nc("@action:label", "Visible settings:")
                                width: (parent.width / 3) | 0
                            }
                            UM.Label
                            {
                                text: catalog.i18nc("@action:label", "%1 out of %2" ).arg(manager.numVisibleSettings).arg(manager.totalNumberOfSettings)
                                width: (parent.width / 3) | 0
                            }
                        }
                    }

                    Row
                    {
                        width: parent.width
                        height: childrenRect.height
                        visible: manager.hasObjectsOnPlate
                        UM.ColorImage
                        {
                            width: warningLabel.height
                            height: width
                            source: UM.Theme.getIcon("Information")
                            color: UM.Theme.getColor("text")
                        }
                        UM.Label
                        {
                            id: warningLabel
                            text: catalog.i18nc("@action:warning", "Loading a project will clear all models on the build plate.")
                        }
                    }
                }
            }
        }
    }

    property bool warning: manager.missingPackages.length > 0

    footerComponent: Rectangle
    {
        color: warning ? UM.Theme.getColor("warning") : "transparent"
        anchors.bottom: parent.bottom
        width: parent.width
        height: childrenRect.height + 2 * workspaceDialog.margin

        Column
        {
            height: childrenRect.height
            spacing: workspaceDialog.margin

            anchors.margins: workspaceDialog.margin
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top

            RowLayout
            {
                id: warningRow
                height: childrenRect.height
                visible: warning
                spacing: workspaceDialog.margin
                UM.ColorImage
                {
                    width: UM.Theme.getSize("extruder_icon").width
                    height: UM.Theme.getSize("extruder_icon").height
                    source: UM.Theme.getIcon("Warning")
                }

                UM.Label
                {
                    id: warningText
                    text: catalog.i18nc("@label", "The material used in this project is currently not installed in Cura.<br/>Install the material profile and reopen the project.")
                }
            }

            Loader
            {
                width: parent.width
                height: childrenRect.height
                sourceComponent: buttonRow
            }
        }
    }

    buttonSpacing: UM.Theme.getSize("wide_margin").width

    rightButtons: [
        Cura.TertiaryButton
        {
            visible: !warning
            text: catalog.i18nc("@action:button", "Cancel")
            onClicked: reject()
        },
        Cura.PrimaryButton
        {
            visible: !warning
            text: catalog.i18nc("@action:button", "Open")
            onClicked: accept()
        },
        Cura.TertiaryButton
        {
            visible: warning
            text: catalog.i18nc("@action:button", "Open project anyway")
            onClicked: {
                manager.showMissingMaterialsWarning();
                accept();
            }
        },
        Cura.PrimaryButton
        {
            visible: warning
            text: catalog.i18nc("@action:button", "Install missing material")
            onClicked: manager.installMissingPackages()
        }
    ]

    onRejected: manager.onCancelButtonClicked()
    onAccepted: manager.onOkButtonClicked()
}
