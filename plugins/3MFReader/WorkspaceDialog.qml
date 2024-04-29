// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtQuick.Window 2.2

import UM 1.6 as UM
import Cura 1.1 as Cura

UM.Dialog
{
    id: workspaceDialog
    title: manager.isUcp? catalog.i18nc("@title:window Don't translate 'Universal Cura Project'", "Open Universal Cura Project (UCP)"): catalog.i18nc("@title:window", "Open Project")

    margin: UM.Theme.getSize("default_margin").width
    minimumWidth: UM.Theme.getSize("modal_window_minimum").width
    minimumHeight: UM.Theme.getSize("modal_window_minimum").height

    backgroundColor: UM.Theme.getColor("detail_background")

    headerComponent: Rectangle
    {
        height: childrenRect.height + 2 * UM.Theme.getSize("default_margin").height
        color: UM.Theme.getColor("main_background")
        ColumnLayout
        {
            id: headerColumn

            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.rightMargin: anchors.leftMargin
            RowLayout
            {
                UM.Label
                {
                    id: titleLabel
                    text: manager.isUcp? catalog.i18nc("@action:title Don't translate 'Universal Cura Project'", "Summary - Open Universal Cura Project (UCP)"): catalog.i18nc("@action:title", "Summary - Cura Project")
                    font: UM.Theme.getFont("large")
                }
                Cura.TertiaryButton
                {
                    id: learnMoreButton
                    visible: manager.isUcp
                    text: catalog.i18nc("@button", "Learn more")
                    iconSource: UM.Theme.getIcon("LinkExternal")
                    isIconOnRightSide: true
                    onClicked: Qt.openUrlExternally("https://support.ultimaker.com/s/article/000002979")
                }
            }
        }
    }

    Rectangle
    {
        anchors.fill: parent
        UM.I18nCatalog { id: catalog; name: "cura" }
        color: UM.Theme.getColor("main_background")

        Flickable
        {
            id: dialogSummaryItem
            width: parent.width
            height: parent.height

            clip: true

            contentHeight: contentColumn.height
            ScrollBar.vertical: UM.ScrollBar { id: scrollbar }

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
                id: contentColumn
                width: parent.width - scrollbar.width - UM.Theme.getSize("default_margin").width
                height: childrenRect.height

                spacing: UM.Theme.getSize("default_margin").height
                leftPadding: UM.Theme.getSize("default_margin").width
                rightPadding: UM.Theme.getSize("default_margin").width

                WorkspaceSection
                {
                    id: printerSection
                    title: catalog.i18nc("@action:label", "Printer settings")
                    iconSource: UM.Theme.getIcon("Printer")
                    content: Column
                    {
                        spacing: UM.Theme.getSize("default_margin").height
                        leftPadding: UM.Theme.getSize("medium_button_icon").width + UM.Theme.getSize("default_margin").width

                        WorkspaceRow
                        {
                            leftLabelText: catalog.i18nc("@action:label", "Type")
                            rightLabelText: manager.machineType
                        }

                        WorkspaceRow
                        {
                            leftLabelText: catalog.i18nc("@action:label", manager.isPrinterGroup ? "Printer Group" : "Printer Name")
                            rightLabelText: manager.isUcp? manager.machineType: manager.machineName == catalog.i18nc("@button", "Create new") ? "" : manager.machineName
                        }
                    }

                    comboboxTitle: catalog.i18nc("@action:label", "Open With")
                    comboboxTooltipText: catalog.i18nc("@info:tooltip", "Printer settings will be updated to match the settings saved with the project.")
                    comboboxVisible: workspaceDialog.visible && manager.updatableMachinesModel.count > 1
                    combobox: Cura.MachineSelector
                    {
                        id: machineSelector
                        headerCornerSide: Cura.RoundedRectangle.Direction.All
                        width: parent.width
                        height: parent.height
                        machineListModel: manager.updatableMachinesModel
                        machineName: manager.machineName

                        isConnectedCloudPrinter: false
                        isCloudRegistered: false
                        isNetworkPrinter: manager.isNetworked
                        isGroup: manager.isAbstractMachine
                        connectionStatus: ""

                        minDropDownWidth: machineSelector.width

                        Component
                        {
                            id: componentNewPrinter

                            Cura.SecondaryButton
                            {
                                id: createNewPrinter
                                text: catalog.i18nc("@button", "Create new")
                                fixedWidthMode: true
                                width: parent.width - leftPadding * 1.5
                                visible: manager.allowCreateMachine
                                onClicked:
                                {
                                    toggleContent()
                                    manager.setResolveStrategy("machine", "new")
                                    machineSelector.machineName = catalog.i18nc("@button", "Create new")
                                    manager.setIsAbstractMachine(false)
                                    manager.setIsNetworkedMachine(false)
                                }
                            }
                        }

                        buttons: manager.allowCreateMachine ? [componentNewPrinter.createObject()] : []

                        onSelectPrinter: function(machine)
                        {
                            toggleContent();
                            machineSelector.machineName = machine.name
                            manager.setResolveStrategy("machine", "override")
                            manager.setMachineToOverride(machine.id)
                            manager.setIsAbstractMachine(machine.isAbstractMachine)
                            manager.setIsNetworkedMachine(machine.isNetworked)
                        }
                    }
                }

                WorkspaceSection
                {
                    id: ucpProfileSection
                    visible: manager.isUcp
                    title: catalog.i18nc("@action:label", "Settings Loaded from UCP file")
                    iconSource: UM.Theme.getIcon("Settings")

                    content: Column
                    {
                        id: ucpProfileSettingsValuesTable
                        spacing: UM.Theme.getSize("default_margin").height
                        leftPadding: UM.Theme.getSize("medium_button_icon").width + UM.Theme.getSize("default_margin").width

                        WorkspaceRow
                        {
                            id: numberOfOverrides
                            leftLabelText: catalog.i18nc("@action:label", "Settings Loaded from UCP file")
                            rightLabelText: catalog.i18ncp("@action:label", "%1 override", "%1 overrides", manager.exportedSettingModelRowCount).arg(manager.exportedSettingModelRowCount)
                            buttonText: tableViewSpecificSettings.shouldBeVisible ? catalog.i18nc("@action:button", "Hide settings") : catalog.i18nc("@action:button", "Show settings")
                            onButtonClicked: tableViewSpecificSettings.shouldBeVisible = !tableViewSpecificSettings.shouldBeVisible
                        }
                        Cura.TableView
                        {
                            id: tableViewSpecificSettings
                            width: parent.width - parent.leftPadding - UM.Theme.getSize("default_margin").width
                            height: UM.Theme.getSize("card").height
                            visible: shouldBeVisible && manager.isUcp
                            property bool shouldBeVisible: true

                            columnHeaders:
                            [
                                catalog.i18nc("@title:column", "Applies on"),
                                catalog.i18nc("@title:column", "Setting"),
                                catalog.i18nc("@title:column", "Value")
                            ]

                            model: UM.TableModel
                            {
                                id: tableModel
                                headers: ["category", "label", "value"]
                                rows: manager.exportedSettingModelItems
                            }

                            Connections
                            {
                                target: manager
                                function onExportedSettingModelChanged()
                                {
                                    tableModel.clear()
                                    tableModel.rows = manager.exportedSettingModelItems
                                }
                            }
                        }
                    }

                    comboboxVisible: manager.qualityChangesConflict
                    combobox: Cura.ComboBox
                    {
                        id: qualityChangesResolveComboBox
                        model: resolveStrategiesModel
                        textRole: "label"
                        visible: manager.qualityChangesConflict && !manager.isUcp
                        contentLeftPadding: UM.Theme.getSize("default_margin").width + UM.Theme.getSize("narrow_margin").width
                        textFont: UM.Theme.getFont("medium")

                        background: Cura.RoundedRectangle
                        {
                            border.width: UM.Theme.getSize("default_lining").width
                            border.color: UM.Theme.getColor("lining")
                            color: qualityChangesResolveComboBox.hovered ? UM.Theme.getColor("expandable_hover") : UM.Theme.getColor("action_button")
                            cornerSide: Cura.RoundedRectangle.Direction.All
                            radius: UM.Theme.getSize("default_radius").width
                        }

                        // This is a hack. This will trigger onCurrentIndexChanged and set the index when this component in loaded
                        currentIndex:
                        {
                            currentIndex = 0
                        }

                        onCurrentIndexChanged:
                        {
                            manager.setResolveStrategy("quality_changes", resolveStrategiesModel.get(currentIndex).key)
                        }
                    }
                }

                WorkspaceSection
                {
                    id: profileSection
                    title: manager.isUcp? catalog.i18nc("@action:label", "Suggested Profile settings"):catalog.i18nc("@action:label", "Profile settings")
                    iconSource: UM.Theme.getIcon("Sliders")
                    content: Column
                    {
                        id: profileSettingsValuesTable
                        spacing: UM.Theme.getSize("default_margin").height
                        leftPadding: UM.Theme.getSize("medium_button_icon").width + UM.Theme.getSize("default_margin").width

                        WorkspaceRow
                        {
                            leftLabelText: catalog.i18nc("@action:label", "Name")
                            rightLabelText: manager.qualityName
                            visible: manager.isCompatibleMachine
                        }

                        WorkspaceRow
                        {
                            leftLabelText: catalog.i18nc("@action:label", "Intent")
                            rightLabelText: manager.intentName
                            visible: manager.isCompatibleMachine
                        }

                        WorkspaceRow
                        {
                            leftLabelText: catalog.i18nc("@action:label", "Not in profile")
                            rightLabelText: catalog.i18ncp("@action:label", "%1 override", "%1 overrides", manager.numUserSettings).arg(manager.numUserSettings)
                            visible: manager.numUserSettings != 0 && !manager.isUcp
                        }

                        WorkspaceRow
                        {
                            leftLabelText: catalog.i18nc("@action:label", "Derivative from")
                            rightLabelText: catalog.i18ncp("@action:label", "%1, %2 override", "%1, %2 overrides", manager.numSettingsOverridenByQualityChanges).arg(manager.qualityType).arg(manager.numSettingsOverridenByQualityChanges)
                            visible: manager.numSettingsOverridenByQualityChanges != 0 && manager.isCompatibleMachine
                        }
                    }
                }

                WorkspaceSection
                {
                    id: materialSection
                    title: manager.isUcp? catalog.i18nc("@action:label", "Suggested Material settings"): catalog.i18nc("@action:label", "Material settings")
                    iconSource: UM.Theme.getIcon("Spool")
                    content: Column
                    {
                        spacing: UM.Theme.getSize("default_margin").height
                        leftPadding: UM.Theme.getSize("medium_button_icon").width + UM.Theme.getSize("default_margin").width

                        Repeater
                        {
                            model: manager.materialLabels
                            delegate: WorkspaceRow
                            {
                                leftLabelText: catalog.i18nc("@action:label", "Name")
                                rightLabelText: modelData
                            }
                        }
                    }

                    comboboxVisible: manager.materialConflict

                    combobox: Cura.ComboBox
                    {
                        id: materialResolveComboBox
                        model: resolveStrategiesModel
                        textRole: "label"
                        visible: manager.materialConflict && !manager.isUcp
                        contentLeftPadding: UM.Theme.getSize("default_margin").width + UM.Theme.getSize("narrow_margin").width
                        textFont: UM.Theme.getFont("medium")

                        background: Cura.RoundedRectangle
                        {
                            border.width: UM.Theme.getSize("default_lining").width
                            border.color: UM.Theme.getColor("lining")
                            color: materialResolveComboBox.hovered ? UM.Theme.getColor("expandable_hover") : UM.Theme.getColor("action_button")
                            cornerSide: Cura.RoundedRectangle.Direction.All
                            radius: UM.Theme.getSize("default_radius").width
                        }

                        // This is a hack. This will trigger onCurrentIndexChanged and set the index when this component in loaded
                        currentIndex:
                        {
                            currentIndex = 0
                        }

                        onCurrentIndexChanged:
                        {
                            manager.setResolveStrategy("material", resolveStrategiesModel.get(currentIndex).key)
                        }
                    }
                }

                WorkspaceSection
                {
                    id: visibilitySection
                    title: catalog.i18nc("@action:label", "Setting visibility")
                    iconSource: UM.Theme.getIcon("Eye")
                    visible : !manager.isUcp
                    content: Column
                    {
                        spacing: UM.Theme.getSize("default_margin").height
                        leftPadding: UM.Theme.getSize("medium_button_icon").width + UM.Theme.getSize("default_margin").width
                        bottomPadding: UM.Theme.getSize("narrow_margin").height

                        WorkspaceRow
                        {
                            leftLabelText: catalog.i18nc("@action:label", "Mode")
                            rightLabelText: manager.activeMode
                        }

                        WorkspaceRow
                        {
                            leftLabelText: catalog.i18nc("@action:label", "%1 out of %2" ).arg(manager.numVisibleSettings).arg(manager.totalNumberOfSettings)
                            rightLabelText: manager.activeMode
                            visible: manager.hasVisibleSettingsField
                        }
                    }
                }

                Row
                {
                    id: clearBuildPlateWarning
                    width: parent.width
                    height: childrenRect.height
                    spacing: UM.Theme.getSize("default_margin").width
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

    property bool warning: manager.missingPackages.length > 0

    footerComponent: Rectangle
    {
        color: warning ? UM.Theme.getColor("warning") : "transparent"
        anchors.bottom: parent.bottom
        width: parent.width
        height: childrenRect.height + (warning ? 2 * workspaceDialog.margin : workspaceDialog.margin)

        Column
        {
            height: childrenRect.height
            spacing: workspaceDialog.margin

            anchors.leftMargin: workspaceDialog.margin
            anchors.rightMargin: workspaceDialog.margin
            anchors.bottomMargin: workspaceDialog.margin
            anchors.topMargin: warning ? workspaceDialog.margin : 0

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
                    text: catalog.i18nc("@label", "This project contains materials or plugins that are currently not installed in Cura.<br/>Install the missing packages and reopen the project.")
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
            text: catalog.i18nc("@action:button", "Install missing packages")
            onClicked: manager.installMissingPackages()
        }
    ]

    onClosing: manager.notifyClosed()
    onRejected: manager.onCancelButtonClicked()
    onAccepted: manager.onOkButtonClicked()
    onVisibleChanged:
    {
        if (visible)
        {
            // Force reload the comboboxes
            // Since this dialog is only created once the first time you open it, these comboxes need to be reloaded
            // each time it is shown after the first time so that the indexes will update correctly.
            materialSection.reloadValues()
            profileSection.reloadValues()
            printerSection.reloadValues()
            ucpProfileSection.reloadValues()
        }
    }
}
