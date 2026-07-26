// Copyright (c) 2026 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick
import QtQuick.Controls

import UM 1.5 as UM
import Cura 1.0 as Cura

import "../Menus"

Item
{
    id: settingsView

    property bool loseFocusOnScrollPositionChange: true
    UM.I18nCatalog { id: catalog; name: "cura" }

    readonly property var settingPreferenceVisibilityHandler: TabbedSettingsManager.getVisibilityHandler("ExtendedSettingPreference")
    readonly property var perCategoryVisibilityHandler:       TabbedSettingsManager.getVisibilityHandler("PerCategory")
    readonly property var instanceContainerVisibilityHandler: TabbedSettingsManager.getVisibilityHandler("InstanceContainer")

    property string selectedKey: "_overview"

    onSelectedKeyChanged:
    {
        clearFilter()

        // Restore overview collapse-state when entering Overview; expand everything otherwise.
        definitionsModel.expanded = (selectedKey === "_overview") ? CuraApplication.expandedCategories : ["*"]

        instanceContainerVisibilityHandler.active = (selectedKey === "_user")
        instanceContainerVisibilityHandler.containerIndex = 0

        if (selectedKey === "_overview")
        {
            definitionsModel.visibilityHandler = settingPreferenceVisibilityHandler
        }
        else if (selectedKey === "_user")
        {
            definitionsModel.visibilityHandler = instanceContainerVisibilityHandler
        }
        else
        {
            perCategoryVisibilityHandler.rootKey = selectedKey
            definitionsModel.visibilityHandler   = perCategoryVisibilityHandler
        }
    }

    Component.onCompleted:
    {
        definitionsModel.visibilityHandler = settingPreferenceVisibilityHandler
        definitionsModel.expanded = CuraApplication.expandedCategories
    }

    function clearFilter()
    {
        settingsSearchTimer.stop()
        filter.text = ""
        filter.editingFinished()
    }

    Item
    {
        id: filterRow

        property bool findingSettings: false

        anchors
        {
            top:   parent.top
            left:  parent.left
            right: parent.right
        }
        height: UM.Theme.getSize("print_setup_big_item").height

            Item
            {
                id: filterContainer

                anchors
                {
                    top:   parent.top
                    left:  parent.left
                    right: settingVisibilityMenu.left
                }
                height: UM.Theme.getSize("print_setup_big_item").height

                Timer
                {
                    id: settingsSearchTimer
                    onTriggered: filter.editingFinished()
                    interval: 500
                    running:  false
                    repeat:   false
                }

                Cura.TextField
                {
                    id: filter
                    height: parent.height
                    anchors.left:  parent.left
                    anchors.right: parent.right
                    topPadding:    height / 4
                    leftPadding:   searchIcon.width + UM.Theme.getSize("default_margin").width * 2
                    placeholderText: catalog.i18nc("@label:textbox", "Search settings")
                    font: UM.Theme.getFont("default_italic")

                    property var  expandedCategories
                    property bool lastFindingSettings: false

                    UM.ColorImage
                    {
                        id: searchIcon
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left:           parent.left
                        anchors.leftMargin:     UM.Theme.getSize("default_margin").width
                        source: UM.Theme.getIcon("Magnifier")
                        height: UM.Theme.getSize("small_button_icon").height
                        width:  height
                        color:  UM.Theme.getColor("text")
                    }

                    onTextChanged: settingsSearchTimer.restart()

                    onEditingFinished:
                    {
                        definitionsModel.filter = {"i18n_label|i18n_description" : "*" + text}
                        filterRow.findingSettings = (text.length > 0)
                        if (filterRow.findingSettings !== lastFindingSettings)
                        {
                            updateDefinitionModel()
                            lastFindingSettings = filterRow.findingSettings
                        }
                    }

                    Keys.onEscapePressed: settingsView.clearFilter()

                    function updateDefinitionModel()
                    {
                        if (filterRow.findingSettings)
                        {
                            expandedCategories = definitionsModel.expanded.slice()
                            definitionsModel.expanded = [""]  // keep closed while building the list
                            definitionsModel.showAncestors = true
                            definitionsModel.showAll       = false  // respect current tab's visibility handler
                            definitionsModel.expanded      = ["*"]
                        }
                        else
                        {
                            if (expandedCategories)
                            {
                                definitionsModel.expanded = expandedCategories
                            }
                            definitionsModel.showAncestors = false
                            definitionsModel.showAll       = false
                        }
                    }
                }

                UM.SimpleButton
                {
                    id: clearFilterButton
                    iconSource: UM.Theme.getIcon("Cancel")
                    visible: filterRow.findingSettings

                    height: Math.round(parent.height * 0.4)
                    width:  visible ? height : 0

                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right:          parent.right
                    anchors.rightMargin:    UM.Theme.getSize("default_margin").width

                    color:      UM.Theme.getColor("setting_control_button")
                    hoverColor: UM.Theme.getColor("setting_control_button_hover")

                    onClicked:
                    {
                        settingsView.clearFilter()
                        filter.forceActiveFocus()
                    }
                }
            }

            SettingVisibilityPresetsMenu
            {
                id: settingVisibilityPresetsMenu
                onCollapseAllCategories:
                {
                    settingsView.clearFilter()
                    definitionsModel.collapseAllCategories()
                }
            }

            UM.BurgerButton
            {
                id: settingVisibilityMenu

                anchors.verticalCenter: filterContainer.verticalCenter
                anchors.right:          parent.right

                onClicked:
                {
                    settingVisibilityPresetsMenu.popup(
                        popupContainer,
                        -settingVisibilityPresetsMenu.width + UM.Theme.getSize("default_margin").width,
                        settingVisibilityMenu.height
                    )
                }
            }

            Item
            {
                // Workaround: prevents the burger button from being rescaled when a popup is attached.
                id: popupContainer
                anchors.bottom: settingVisibilityMenu.bottom
                anchors.right:  settingVisibilityMenu.right
            }
        }

    MouseArea
    {
        anchors.fill:    contents
        acceptedButtons: Qt.AllButtons
        onWheel: function(wheel) { wheel.accepted = true }
    }

    ListView
    {
        id: contents
        maximumFlickVelocity: 1000 * screenScaleFactor
        clip:        true
        cacheBuffer: 1000000   // Cache everything to avoid reloads while scrolling.

        anchors
        {
            top:        filterRow.bottom
            topMargin:  UM.Theme.getSize("default_margin").height
            bottom:     parent.bottom
            right:      parent.right
            left:       parent.left
        }

        ScrollBar.vertical: UM.ScrollBar
        {
            id: scrollBar
            onPositionChanged:
            {
                // Remove focus from controls while scrolling so combo-box dropdowns close.
                if (!activeFocus && !filter.activeFocus && loseFocusOnScrollPositionChange)
                {
                    forceActiveFocus()
                }
            }
        }

        model: UM.SettingDefinitionsModel
        {
            id: definitionsModel
            containerId: Cura.MachineManager.activeMachine !== null ? Cura.MachineManager.activeMachine.definition.id : ""
            // Initial handler is the preference (favorites) handler; switched by onSelectedKeyChanged.
            visibilityHandler: UM.SettingPreferenceVisibilityHandler {}
            exclude: ["machine_settings", "command_line_settings", "ppr",
                        "infill_mesh", "infill_mesh_order", "cutting_mesh", "support_mesh", "anti_overhang_mesh"]
            onExpandedChanged:
            {
                if (!filterRow.findingSettings && selectedKey === "_overview")
                {
                    CuraApplication.setExpandedCategories(expanded)
                }
            }
            onVisibilityChanged: Cura.SettingInheritanceManager.scheduleUpdate()
        }

        property int    indexWithFocus:  -1
        property string activeMachineId: Cura.MachineManager.activeMachine !== null ? Cura.MachineManager.activeMachine.id : ""

        delegate: Loader
        {
            id: delegate

            width:   contents.width - (scrollBar.width + UM.Theme.getSize("narrow_margin").width)
            // In the Changed Settings tab show every changed setting, even if its parent is disabled.
            opacity: (selectedKey === "_user" || enabled) ? 1 : 0
            enabled: selectedKey === "_user" || provider.properties.enabled === "True"

            property var  definition:             model
            property var  settingDefinitionsModel: definitionsModel
            property var  propertyProvider:        provider
            property var  globalPropertyProvider:  inheritStackProvider
            property bool externalResetHandler:    false

            // Disable async loading for types that break when loaded asynchronously.
            asynchronous: model.type !== "enum" && model.type !== "extruder" && model.type !== "optional_extruder"
            active: model.type !== undefined

            // Reactively disable depth indentation for the flat Changed-settings list.
            // A Binding (not onLoaded) is required so it re-applies when cached delegates are reused.
            Binding
            {
                target:   delegate.item
                property: "doDepthIndentation"
                value:    selectedKey !== "_user"
                when:     delegate.status === Loader.Ready
            }

            source:
            {
                switch (model.type)
                {
                    case "int":              return "SettingTextField.qml"
                    case "[int]":            return "SettingTextField.qml"
                    case "float":            return "SettingTextField.qml"
                    case "enum":             return "SettingComboBox.qml"
                    case "extruder":         return "SettingExtruder.qml"
                    case "bool":             return "SettingCheckBox.qml"
                    case "str":              return "SettingTextField.qml"
                    case "optional_extruder": return "SettingOptionalExtruder.qml"
                    case "category":
                        return selectedKey === "_overview" ? "SettingCategory.qml" : "CategoryHeader.qml"
                    default:                 return "SettingUnknown.qml"
                }
            }

            // Keep containerStackId in sync with the active extruder / limit_to_extruder.
            Binding
            {
                target:   provider
                property: "containerStackId"
                when: model.settable_per_extruder ||
                        (inheritStackProvider.properties.limit_to_extruder !== undefined &&
                        inheritStackProvider.properties.limit_to_extruder >= 0)
                value:
                {
                    if (!model.settable_per_extruder)
                    {
                        return contents.activeMachineId
                    }
                    if (inheritStackProvider.properties.limit_to_extruder !== undefined &&
                        inheritStackProvider.properties.limit_to_extruder >= 0)
                    {
                        return Cura.ExtruderManager.extruderIds[inheritStackProvider.properties.limit_to_extruder]
                    }
                    if (Cura.ExtruderManager.activeExtruderStackId)
                    {
                        return Cura.ExtruderManager.activeExtruderStackId
                    }
                    return contents.activeMachineId
                }
            }

            UM.SettingPropertyProvider
            {
                id: inheritStackProvider
                containerStackId: contents.activeMachineId
                key:              model.key
                watchedProperties: ["limit_to_extruder"]
            }

            UM.SettingPropertyProvider
            {
                id: provider
                containerStackId: contents.activeMachineId
                key:              model.key
                watchedProperties: ["value", "enabled", "state", "validationState",
                                    "settable_per_extruder", "resolve", "unit"]
                storeIndex:       0
                removeUnusedValue: model.resolve === undefined
            }

            Connections
            {
                target: item

                function onContextMenuRequested()
                {
                    contextMenu.key           = model.key
                    contextMenu.settingVisible = settingPreferenceVisibilityHandler.getSettingVisible(model.key)
                    contextMenu.provider       = provider
                    contextMenu.popup()
                }
                function onShowTooltip(text)
                {
                    base.showTooltip(delegate, Qt.point(-settingsView.x - UM.Theme.getSize("default_margin").width, 0), text)
                }
                function onHideTooltip() { base.hideTooltip() }
                function onShowAllHiddenInheritedSettings(category_id)
                {
                    var children_with_override = Cura.SettingInheritanceManager.getChildrenKeysWithOverride(category_id)
                    for (var i = 0; i < children_with_override.length; i++)
                    {
                        definitionsModel.setVisible(children_with_override[i], true)
                    }
                    Cura.SettingInheritanceManager.manualRemoveOverride(category_id)
                }
                function onFocusReceived()
                {
                    contents.indexWithFocus = index
                    contents.positionViewAtIndex(index, ListView.Contain)
                }
                function onSetActiveFocusToNextSetting(forward)
                {
                    if (forward === undefined || forward)
                    {
                        contents.currentIndex = contents.indexWithFocus + 1
                        while (contents.currentItem && contents.currentItem.height <= 0)
                        {
                            contents.currentIndex++
                        }
                        if (contents.currentItem)
                        {
                            contents.currentItem.item.focusItem.forceActiveFocus()
                        }
                    }
                    else
                    {
                        contents.currentIndex = contents.indexWithFocus - 1
                        while (contents.currentItem && contents.currentItem.height <= 0)
                        {
                            contents.currentIndex--
                        }
                        if (contents.currentItem)
                        {
                            contents.currentItem.item.focusItem.forceActiveFocus()
                        }
                    }
                }
                function onSetScrollPositionChangeLoseFocus(lose_focus)
                {
                    settingsView.loseFocusOnScrollPositionChange = lose_focus
                }
            }
        }

        Cura.Menu
        {
            id: contextMenu

            property string key
            property var    provider
            property bool   settingVisible

            Cura.MenuItem
            {
                //: Settings context menu action
                text:    catalog.i18nc("@action:menu", "Copy value to all extruders")
                visible: machineExtruderCount.properties.value > 1
                enabled: contextMenu.provider !== undefined &&
                            contextMenu.provider.properties.settable_per_extruder !== "False"
                onTriggered: Cura.MachineManager.copyValueToExtruders(contextMenu.key)
            }

            Cura.MenuItem
            {
                //: Settings context menu action
                text:    catalog.i18nc("@action:menu", "Copy all changed values to all extruders")
                visible: machineExtruderCount.properties.value > 1
                enabled: contextMenu.provider !== undefined
                onTriggered: Cura.MachineManager.copyAllValuesToExtruders()
            }

            Cura.MenuSeparator { visible: machineExtruderCount.properties.value > 1 }

            Instantiator
            {
                id: customMenuItems
                model: Cura.SidebarCustomMenuItemsModel {}
                Cura.MenuItem
                {
                    text: model.name
                    onTriggered:
                    {
                        customMenuItems.model.callMenuItemMethod(name, model.actions, {"key": contextMenu.key})
                    }
                }
                onObjectAdded: function(index, object)
                {
                    contextMenu.insertItem(index, object)
                    if (Qt.platform.os === "osx") object.text += " "
                }
                onObjectRemoved: function(index, object) { contextMenu.removeItem(object) }
            }

            Cura.MenuSeparator { visible: customMenuItems.count > 0 }

            Cura.MenuItem
            {
                text:
                {
                    return contextMenu.settingVisible
                        ? catalog.i18nc("@action:menu", "Remove from visible settings")
                        : catalog.i18nc("@action:menu", "Add to visible settings")
                }
                onTriggered:
                {
                    settingPreferenceVisibilityHandler.setSettingVisible(contextMenu.key, !contextMenu.settingVisible)
                }
            }

            Cura.MenuItem
            {
                text: catalog.i18nc("@action:menu", "Configure visible settings...")
                onTriggered: Cura.Actions.configureSettingVisibility.trigger(contextMenu)
            }
        }

        UM.SettingPropertyProvider
        {
            id: machineExtruderCount
            containerStackId: Cura.MachineManager.activeMachine !== null ? Cura.MachineManager.activeMachine.id : ""
            key:              "machine_extruder_count"
            watchedProperties: ["value"]
            storeIndex:       0
        }
    }

    Item
    {
        anchors
        {
            top:       filterRow.bottom
            topMargin: UM.Theme.getSize("default_margin").height
            left:      parent.left
            right:     parent.right
            bottom:    parent.bottom
        }
        visible: selectedKey === "_user" && contents.count === 0

        UM.Label
        {
            anchors.centerIn: parent
            width: parent.width - 2 * UM.Theme.getSize("default_margin").width
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@info:status",
                "No settings have been changed from the active profile defaults.")
            color: UM.Theme.getColor("text_inactive")
        }
    }
}
