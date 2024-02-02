//Copyright (c) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15

import UM 1.5 as UM
import Cura 1.0 as Cura
import ".."


Item
{
    id: base
    width: childrenRect.width
    height: childrenRect.height
    property var allCategoriesExceptSupport: [ "machine_settings", "resolution", "shell", "infill", "material", "speed",
                                    "travel", "cooling", "platform_adhesion", "dual", "meshfix", "blackmagic", "experimental"]

    readonly property string normalMeshType: ""
    readonly property string supportMeshType: "support_mesh"
    readonly property string cuttingMeshType: "cutting_mesh"
    readonly property string infillMeshType: "infill_mesh"
    readonly property string antiOverhangMeshType: "anti_overhang_mesh"

    property var currentMeshType: UM.Controller.properties.getValue("MeshType")

    // Update the view every time the currentMeshType changes
    onCurrentMeshTypeChanged:
    {
        var type = currentMeshType

        // set checked state of mesh type buttons
        updateMeshTypeCheckedState(type)

        // update active type label
        for (var button in meshTypeButtons.children)
        {
            if (meshTypeButtons.children[button].checked)
            {
                meshTypeLabel.text = catalog.i18nc("@label", "Mesh Type") + ": " + meshTypeButtons.children[button].text
                break
            }
        }
        visibility_handler.addSkipResetSetting(currentMeshType)
    }

    function updateMeshTypeCheckedState(type)
    {
        // set checked state of mesh type buttons
        normalButton.checked = type === normalMeshType
        supportMeshButton.checked = type === supportMeshType
        overlapMeshButton.checked = type === infillMeshType || type === cuttingMeshType
        antiOverhangMeshButton.checked = type === antiOverhangMeshType
    }

    function setMeshType(type)
    {
        UM.Controller.setProperty("MeshType", type)
        updateMeshTypeCheckedState(type)
    }

    UM.I18nCatalog { id: catalog; name: "cura"}

    Column
    {
        id: items
        anchors.top: parent.top;
        anchors.left: parent.left;

        spacing: UM.Theme.getSize("default_margin").height

        Row // Mesh type buttons
        {
            id: meshTypeButtons
            spacing: UM.Theme.getSize("default_margin").width

            UM.ToolbarButton
            {
                id: normalButton
                text: catalog.i18nc("@label", "Normal model")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("Infill0")
                    color: UM.Theme.getColor("icon")
                }
                property bool needBorder: true
                checkable: true
                onClicked: setMeshType(normalMeshType);
                z: 4
            }

            UM.ToolbarButton
            {
                id: supportMeshButton
                text: catalog.i18nc("@label", "Print as support")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("MeshTypeSupport")
                    color: UM.Theme.getColor("icon")
                }
                property bool needBorder: true
                checkable:true
                onClicked: setMeshType(supportMeshType)
                z: 3
            }

            UM.ToolbarButton
            {
                id: overlapMeshButton
                text: catalog.i18nc("@label", "Modify settings for overlaps")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("MeshTypeIntersect")
                    color: UM.Theme.getColor("icon")
                }
                property bool needBorder: true
                checkable:true
                onClicked: setMeshType(infillMeshType)
                z: 2
            }

            UM.ToolbarButton
            {
                id: antiOverhangMeshButton
                text:  catalog.i18nc("@label", "Don't support overlaps")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("BlockSupportOverlaps")
                    color: UM.Theme.getColor("icon")
                }
                property bool needBorder: true
                checkable: true
                onClicked: setMeshType(antiOverhangMeshType)
                z: 1
            }

        }

        UM.Label
        {
            id: meshTypeLabel
            height: UM.Theme.getSize("setting").height
        }


        Cura.ComboBox
        {
            id: infillOnlyComboBox
            width: parent.width / 2 - UM.Theme.getSize("default_margin").width
            height: UM.Theme.getSize("setting_control").height
            textRole: "text"
            forceHighlight: base.hovered

            model: ListModel
            {
                id: infillOnlyComboBoxModel

                Component.onCompleted: {
                    append({ text: catalog.i18nc("@item:inlistbox", "Infill mesh only") })
                    append({ text: catalog.i18nc("@item:inlistbox", "Cutting mesh") })
                }
            }

            visible: currentMeshType === infillMeshType || currentMeshType === cuttingMeshType


            onActivated:
            {
                setMeshType(index === 0 ? infillMeshType : cuttingMeshType);
            }

            Binding
            {
                target: infillOnlyComboBox
                property: "currentIndex"
                value: currentMeshType === infillMeshType ? 0 : 1
            }
        }

        Column // List of selected Settings to override for the selected object
        {
            // This is to ensure that the panel is first increasing in size up to 200 and then shows a scrollbar.
            // It kinda looks ugly otherwise (big panel, no content on it)
            id: currentSettings
            property int maximumHeight: 200 * screenScaleFactor
            height: Math.min(contents.count * (UM.Theme.getSize("section").height + UM.Theme.getSize("narrow_margin").height + UM.Theme.getSize("default_lining").height), maximumHeight)
            visible: currentMeshType != "anti_overhang_mesh"

            ListView
            {
                id: contents
                height: parent.height
                width: UM.Theme.getSize("setting").width + UM.Theme.getSize("default_margin").width

                ScrollBar.vertical: UM.ScrollBar { id: scrollBar }
                clip: true
                spacing: UM.Theme.getSize("default_lining").height

                model: UM.SettingDefinitionsModel
                {
                    id: addedSettingsModel
                    containerId: Cura.MachineManager.activeMachine !== null ? Cura.MachineManager.activeMachine.definition.id: ""
                    expanded: ["*"]
                    filter:
                    {
                        if (printSequencePropertyProvider.properties.value === "one_at_a_time")
                        {
                            return { settable_per_meshgroup: true }
                        }
                        return { settable_per_meshgroup: true }
                    }
                    exclude:
                    {
                        const excluded_settings = ["support_mesh", "anti_overhang_mesh", "cutting_mesh", "infill_mesh"]

                        if (currentMeshType === "support_mesh")
                        {
                            excluded_settings = excluded_settings.concat(base.allCategoriesExceptSupport)
                        }
                        return excluded_settings
                    }

                    visibilityHandler: Cura.PerObjectSettingVisibilityHandler
                    {
                        id: visibility_handler
                        selectedObjectId: UM.Controller.properties.getValue("SelectedObjectId")
                    }

                    // For some reason the model object is updated after removing him from the memory and
                    // it happens only on Windows. For this reason, set the destroyed value manually.
                    Component.onDestruction:
                    {
                        setDestroyed(true)
                    }
                }
                property int indexWithFocus: -1
                delegate: Row
                {
                    spacing: UM.Theme.getSize("default_margin").width
                    property var settingLoaderItem: settingLoader.item
                    Loader
                    {
                        id: settingLoader
                        width: UM.Theme.getSize("setting").width - removeButton.width - scrollBar.width
                        enabled: provider.properties.enabled === "True"
                        property var definition: model
                        property var settingDefinitionsModel: addedSettingsModel
                        property var propertyProvider: provider
                        property var globalPropertyProvider: inheritStackProvider
                        property var externalResetHandler: false

                        //Qt5.4.2 and earlier has a bug where this causes a crash: https://bugreports.qt.io/browse/QTBUG-35989
                        //In addition, while it works for 5.5 and higher, the ordering of the actual combo box drop down changes,
                        //causing nasty issues when selecting different options. So disable asynchronous loading of enum type completely.
                        asynchronous: model.type !== "enum" && model.type !== "extruder"

                        onLoaded:
                        {
                            settingLoader.item.showRevertButton = false
                            settingLoader.item.showInheritButton = false
                            settingLoader.item.showLinkedSettingIcon = false
                            settingLoader.item.doDepthIndentation = false
                            settingLoader.item.doQualityUserSettingEmphasis = false
                            settingLoader.item.height = UM.Theme.getSize("setting").height + UM.Theme.getSize("narrow_margin").height
                        }

                        sourceComponent:
                        {
                            switch(model.type)
                            {
                                case "int":
                                    return settingTextField
                                case "[int]":
                                    return settingTextField
                                case "float":
                                    return settingTextField
                                case "enum":
                                    return settingComboBox
                                case "extruder":
                                    return settingExtruder
                                case "optional_extruder":
                                    return settingOptionalExtruder
                                case "bool":
                                    return settingCheckBox
                                case "str":
                                    return settingTextField
                                case "category":
                                    return settingCategory
                                default:
                                    return settingUnknown
                            }
                        }
                    }

                    Button
                    {
                        id: removeButton
                        width: UM.Theme.getSize("setting").height
                        height: UM.Theme.getSize("setting").height + UM.Theme.getSize("narrow_margin").height

                        onClicked: addedSettingsModel.setVisible(model.key, false)

                        background: Item
                        {
                            UM.ColorImage
                            {
                                anchors.verticalCenter: parent.verticalCenter
                                width: parent.width
                                height: width
                                color: parent.hovered ? UM.Theme.getColor("setting_control_button_hover") : UM.Theme.getColor("setting_control_button")
                                source: UM.Theme.getIcon("Minus")
                            }
                        }
                    }

                    // Specialty provider that only watches global_inherits (we can't filter on what property changed we get events
                    // so we bypass that to make a dedicated provider).
                    UM.SettingPropertyProvider
                    {
                        id: provider

                        containerStackId: UM.Controller.properties.getValue("ContainerID")
                        key: model.key
                        watchedProperties: [ "value", "enabled", "validationState" ]
                        storeIndex: 0
                        removeUnusedValue: false
                    }

                    UM.SettingPropertyProvider
                    {
                        id: inheritStackProvider
                        containerStackId: UM.Controller.properties.getValue("ContainerID")
                        key: model.key
                        watchedProperties: [ "limit_to_extruder" ]
                    }

                    Connections
                    {
                        target: inheritStackProvider
                        function onPropertiesChanged() { provider.forcePropertiesChanged() }
                    }

                    Connections
                    {
                        target: settingLoader.item
                        function onFocusReceived()
                        {

                            contents.indexWithFocus = index
                            contents.positionViewAtIndex(index, ListView.Contain)
                        }
                        function onSetActiveFocusToNextSetting(forward)
                        {
                            if (forward == undefined || forward)
                            {
                                contents.currentIndex = contents.indexWithFocus + 1
                                while(contents.currentItem && contents.currentItem.height <= 0)
                                {
                                    contents.currentIndex++
                                }
                                if (contents.currentItem)
                                {
                                    contents.currentItem.settingLoaderItem.focusItem.forceActiveFocus()
                                }
                            }
                            else
                            {
                                contents.currentIndex = contents.indexWithFocus - 1
                                while(contents.currentItem && contents.currentItem.height <= 0)
                                {
                                    contents.currentIndex--
                                }
                                if (contents.currentItem)
                                {
                                    contents.currentItem.settingLoaderItem.focusItem.forceActiveFocus()
                                }
                            }
                        }
                    }

                    Connections
                    {
                        target: UM.Controller
                        function onPropertiesChanged()
                        {
                            // the values cannot be bound with UM.Controller.properties.getValue() calls,
                            // so here we connect to the signal and update the those values.
                            if (typeof UM.Controller.properties.getValue("SelectedObjectId") !== "undefined")
                            {
                                const selectedObjectId = UM.Controller.properties.getValue("SelectedObjectId")
                                if (addedSettingsModel.visibilityHandler.selectedObjectId != selectedObjectId)
                                {
                                    addedSettingsModel.visibilityHandler.selectedObjectId = selectedObjectId
                                }
                            }
                            if (typeof UM.Controller.properties.getValue("ContainerID") !== "undefined")
                            {
                                const containerId = UM.Controller.properties.getValue("ContainerID")
                                if (provider.containerStackId !== containerId)
                                {
                                    provider.containerStackId = containerId
                                }
                                if (inheritStackProvider.containerStackId !== containerId)
                                {
                                    inheritStackProvider.containerStackId = containerId
                                }
                            }
                        }
                    }
                }
            }
        }

        Cura.SecondaryButton
        {
            id: customiseSettingsButton;
            height: UM.Theme.getSize("setting_control").height;
            visible: currentSettings.visible

            text: catalog.i18nc("@action:button", "Select settings");

            onClicked:
            {
                settingPickDialog.visible = true;
                if (currentMeshType === "support_mesh")
                {
                    settingPickDialog.additional_excluded_settings = base.allCategoriesExceptSupport;
                }
                else
                {
                    settingPickDialog.additional_excluded_settings = [];
                }
            }
        }

    }

    SettingPickDialog
    {
        id: settingPickDialog
    }

    UM.SettingPropertyProvider
    {
        id: machineExtruderCount

        containerStack: Cura.MachineManager.activeMachine
        key: "machine_extruder_count"
        watchedProperties: ["value"]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: printSequencePropertyProvider

        containerStack: Cura.MachineManager.activeMachine
        key: "print_sequence"
        watchedProperties: ["value"]
        storeIndex: 0
    }

    Component { id: settingTextField; Cura.SettingTextField { } }
    Component { id: settingComboBox; Cura.SettingComboBox { } }
    Component { id: settingExtruder; Cura.SettingExtruder { } }
    Component { id: settingOptionalExtruder; Cura.SettingOptionalExtruder { } }
    Component { id: settingCheckBox; Cura.SettingCheckBox { } }
    Component { id: settingCategory; Cura.SettingCategory { } }
    Component { id: settingUnknown; Cura.SettingUnknown { } }
}
