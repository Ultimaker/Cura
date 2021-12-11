// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.2

import UM 1.2 as UM
import Cura 1.0 as Cura

import "../Menus"

Item
{
    id: settingsView

    property QtObject settingVisibilityPresetsModel: CuraApplication.getSettingVisibilityPresetsModel()
    property Action configureSettings
    property bool findingSettings

    Item
    {
        id: filterContainer

        anchors
        {
            top: parent.top
            left: parent.left
            right: settingVisibilityMenu.left
            rightMargin: UM.Theme.getSize("default_margin").width
        }
        height: UM.Theme.getSize("print_setup_big_item").height

        Timer
        {
            id: settingsSearchTimer
            onTriggered: filter.editingFinished()
            interval: 500
            running: false
            repeat: false
        }

        Cura.TextField
        {
            id: filter
            height: parent.height
            anchors.left: parent.left
            anchors.right: parent.right
            leftPadding: searchIcon.width + UM.Theme.getSize("default_margin").width * 2
            placeholderText:  catalog.i18nc("@label:textbox", "Search settings")
            font.italic: true

            property var expandedCategories
            property bool lastFindingSettings: false

            UM.RecolorImage
            {
                id: searchIcon

                anchors
                {
                    verticalCenter: parent.verticalCenter
                    left: parent.left
                    leftMargin: UM.Theme.getSize("default_margin").width
                }
                source: UM.Theme.getIcon("search")
                height: UM.Theme.getSize("small_button_icon").height
                width: height
                color: UM.Theme.getColor("text")
            }

            onTextChanged:
            {
                settingsSearchTimer.restart()
            }

            onEditingFinished:
            {
                definitionsModel.filter = {"i18n_label|i18n_description" : "*" + text}
                findingSettings = (text.length > 0)
                if (findingSettings != lastFindingSettings)
                {
                    updateDefinitionModel()
                    lastFindingSettings = findingSettings
                }
            }

            Keys.onEscapePressed:
            {
                filter.text = ""
            }

            function updateDefinitionModel()
            {
                if (findingSettings)
                {
                    expandedCategories = definitionsModel.expanded.slice()
                    definitionsModel.expanded = [""]  // keep categories closed while to prevent render while making settings visible one by one
                    definitionsModel.showAncestors = true
                    definitionsModel.showAll = true
                    definitionsModel.expanded = ["*"]
                }
                else
                {
                    if (expandedCategories)
                    {
                        definitionsModel.expanded = expandedCategories
                    }
                    definitionsModel.showAncestors = false
                    definitionsModel.showAll = false
                }
            }
        }

        UM.SimpleButton
        {
            id: clearFilterButton
            iconSource: UM.Theme.getIcon("Cancel")
            visible: findingSettings

            height: Math.round(parent.height * 0.4)
            width: visible ? height : 0

            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width

            color: UM.Theme.getColor("setting_control_button")
            hoverColor: UM.Theme.getColor("setting_control_button_hover")

            onClicked:
            {
                filter.text = ""
                filter.forceActiveFocus()
            }
        }
    }

    SettingVisibilityPresetsMenu
    {
        id: settingVisibilityPresetsMenu
        x: settingVisibilityMenu.x
        y: settingVisibilityMenu.y
        onCollapseAllCategories:
        {
            settingsSearchTimer.stop()
            filter.text = "" // clear search field
            filter.editingFinished()
            definitionsModel.collapseAllCategories()
        }
    }

    ToolButton
    {
        id: settingVisibilityMenu

        anchors
        {
            top: filterContainer.top
            bottom: filterContainer.bottom
            right: parent.right
            rightMargin: UM.Theme.getSize("wide_margin").width
        }
        width: UM.Theme.getSize("medium_button_icon").width
        height: UM.Theme.getSize("medium_button_icon").height

        style: ButtonStyle
        {
            background: Item
            {
                UM.RecolorImage
                {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: UM.Theme.getSize("medium_button_icon").width
                    height: UM.Theme.getSize("medium_button_icon").height
                    sourceSize.width: width
                    sourceSize.height: height
                    color: control.hovered ? UM.Theme.getColor("small_button_text_hover") : UM.Theme.getColor("small_button_text")
                    source: UM.Theme.getIcon("Hamburger")
                }
            }
            label: Label {}
        }

        onClicked:
        {
            settingVisibilityPresetsMenu.popup(
                settingVisibilityMenu,
                -settingVisibilityPresetsMenu.width + UM.Theme.getSize("default_margin").width,
                settingVisibilityMenu.height
            )
        }
    }

    // Mouse area that gathers the scroll events to not propagate it to the main view.
    MouseArea
    {
        anchors.fill: scrollView
        acceptedButtons: Qt.AllButtons
        onWheel: wheel.accepted = true
    }

    ScrollView
    {
        id: scrollView
        anchors
        {
            top: filterContainer.bottom
            topMargin: UM.Theme.getSize("default_margin").height
            bottom: parent.bottom
            right: parent.right
            left: parent.left
        }

        style: UM.Theme.styles.scrollview
        flickableItem.flickableDirection: Flickable.VerticalFlick
        __wheelAreaScrollSpeed: 75  // Scroll three lines in one scroll event

        ListView
        {
            id: contents
            cacheBuffer: 1000000   // Set a large cache to effectively just cache every list item.

            model: UM.SettingDefinitionsModel
            {
                id: definitionsModel
                containerId: Cura.MachineManager.activeMachine !== null ? Cura.MachineManager.activeMachine.definition.id: ""
                visibilityHandler: UM.SettingPreferenceVisibilityHandler { }
                exclude: ["machine_settings", "command_line_settings", "infill_mesh", "infill_mesh_order", "cutting_mesh", "support_mesh", "anti_overhang_mesh"] // TODO: infill_mesh settings are excluded hardcoded, but should be based on the fact that settable_globally, settable_per_meshgroup and settable_per_extruder are false.
                expanded: CuraApplication.expandedCategories
                onExpandedChanged:
                {
                    if (!findingSettings)
                    {
                        // Do not change expandedCategories preference while filtering settings
                        // because all categories are expanded while filtering
                        CuraApplication.setExpandedCategories(expanded)
                    }
                }
                onVisibilityChanged: Cura.SettingInheritanceManager.scheduleUpdate()
            }

            property int indexWithFocus: -1
            property double delegateHeight: UM.Theme.getSize("section").height + 2 * UM.Theme.getSize("default_lining").height
            property string activeMachineId: Cura.MachineManager.activeMachine !== null ? Cura.MachineManager.activeMachine.id : ""
            delegate: Loader
            {
                id: delegate

                width: scrollView.width
                height: enabled ? contents.delegateHeight: 0
                Behavior on height { NumberAnimation { duration: 100 } }
                opacity: enabled ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: 100 } }
                enabled: provider.properties.enabled === "True"

                property var definition: model
                property var settingDefinitionsModel: definitionsModel
                property var propertyProvider: provider
                property var globalPropertyProvider: inheritStackProvider
                property bool externalResetHandler: false

                //Qt5.4.2 and earlier has a bug where this causes a crash: https://bugreports.qt.io/browse/QTBUG-35989
                //In addition, while it works for 5.5 and higher, the ordering of the actual combo box drop down changes,
                //causing nasty issues when selecting different options. So disable asynchronous loading of enum type completely.
                asynchronous: model.type !== "enum" && model.type !== "extruder" && model.type !== "optional_extruder"
                active: model.type !== undefined

                source:
                {
                    switch(model.type)
                    {
                        case "int":
                            return "SettingTextField.qml"
                        case "[int]":
                            return "SettingTextField.qml"
                        case "float":
                            return "SettingTextField.qml"
                        case "enum":
                            return "SettingComboBox.qml"
                        case "extruder":
                            return "SettingExtruder.qml"
                        case "bool":
                            return "SettingCheckBox.qml"
                        case "str":
                            return "SettingTextField.qml"
                        case "category":
                            return "SettingCategory.qml"
                        case "optional_extruder":
                            return "SettingOptionalExtruder.qml"
                        default:
                            return "SettingUnknown.qml"
                    }
                }

                // Binding to ensure that the right containerstack ID is set for the provider.
                // This ensures that if a setting has a limit_to_extruder id (for instance; Support speed points to the
                // extruder that actually prints the support, as that is the setting we need to use to calculate the value)
                Binding
                {
                    target: provider
                    property: "containerStackId"
                    when: model.settable_per_extruder || (inheritStackProvider.properties.limit_to_extruder !== undefined && inheritStackProvider.properties.limit_to_extruder >= 0);
                    value:
                    {
                        // Associate this binding with Cura.MachineManager.activeMachine.id in the beginning so this
                        // binding will be triggered when activeMachineId is changed too.
                        // Otherwise, if this value only depends on the extruderIds, it won't get updated when the
                        // machine gets changed.

                        if (!model.settable_per_extruder)
                        {
                            //Not settable per extruder or there only is global, so we must pick global.
                            return contents.activeMachineId
                        }
                        if (inheritStackProvider.properties.limit_to_extruder !== undefined && inheritStackProvider.properties.limit_to_extruder >= 0)
                        {
                            //We have limit_to_extruder, so pick that stack.
                            return Cura.ExtruderManager.extruderIds[inheritStackProvider.properties.limit_to_extruder];
                        }
                        if (Cura.ExtruderManager.activeExtruderStackId)
                        {
                            //We're on an extruder tab. Pick the current extruder.
                            return Cura.ExtruderManager.activeExtruderStackId;
                        }
                        //No extruder tab is selected. Pick the global stack. Shouldn't happen any more since we removed the global tab.
                        return contents.activeMachineId
                    }
                }

                // Specialty provider that only watches global_inherits (we can't filter on what property changed we get events
                // so we bypass that to make a dedicated provider).
                UM.SettingPropertyProvider
                {
                    id: inheritStackProvider
                    containerStackId: contents.activeMachineId
                    key: model.key
                    watchedProperties: [ "limit_to_extruder" ]
                }

                UM.SettingPropertyProvider
                {
                    id: provider

                    containerStackId: contents.activeMachineId
                    key: model.key
                    watchedProperties: [ "value", "enabled", "state", "validationState", "settable_per_extruder", "resolve" ]
                    storeIndex: 0
                    removeUnusedValue: model.resolve === undefined
                }

                Connections
                {
                    target: item
                    function onContextMenuRequested()
                    {
                        contextMenu.key = model.key;
                        contextMenu.settingVisible = model.visible;
                        contextMenu.provider = provider
                        contextMenu.popup();
                    }
                    function onShowTooltip(text) { base.showTooltip(delegate, Qt.point(-settingsView.x - UM.Theme.getSize("default_margin").width, 0), text) }
                    function onHideTooltip() { base.hideTooltip() }
                    function onShowAllHiddenInheritedSettings()
                    {
                        var children_with_override = Cura.SettingInheritanceManager.getChildrenKeysWithOverride(category_id)
                        for(var i = 0; i < children_with_override.length; i++)
                        {
                            definitionsModel.setVisible(children_with_override[i], true)
                        }
                        Cura.SettingInheritanceManager.manualRemoveOverride(category_id)
                    }
                    function onFocusReceived()
                    {
                        contents.indexWithFocus = index;
                        animateContentY.from = contents.contentY;
                        contents.positionViewAtIndex(index, ListView.Contain);
                        animateContentY.to = contents.contentY;
                        animateContentY.running = true;
                    }
                    function onSetActiveFocusToNextSetting(forward)
                    {
                        if (forward == undefined || forward)
                        {
                            contents.currentIndex = contents.indexWithFocus + 1;
                            while(contents.currentItem && contents.currentItem.height <= 0)
                            {
                                contents.currentIndex++;
                            }
                            if (contents.currentItem)
                            {
                                contents.currentItem.item.focusItem.forceActiveFocus();
                            }
                        }
                        else
                        {
                            contents.currentIndex = contents.indexWithFocus - 1;
                            while(contents.currentItem && contents.currentItem.height <= 0)
                            {
                                contents.currentIndex--;
                            }
                            if (contents.currentItem)
                            {
                                contents.currentItem.item.focusItem.forceActiveFocus();
                            }
                        }
                    }
                }
            }

            NumberAnimation {
                id: animateContentY
                target: contents
                property: "contentY"
                duration: 50
            }

            add: Transition {
                SequentialAnimation {
                    NumberAnimation { properties: "height"; from: 0; duration: 100 }
                    NumberAnimation { properties: "opacity"; from: 0; duration: 100 }
                }
            }
            remove: Transition {
                SequentialAnimation {
                    NumberAnimation { properties: "opacity"; to: 0; duration: 100 }
                    NumberAnimation { properties: "height"; to: 0; duration: 100 }
                }
            }
            addDisplaced: Transition {
                NumberAnimation { properties: "x,y"; duration: 100 }
            }
            removeDisplaced: Transition {
                SequentialAnimation {
                    PauseAnimation { duration: 100; }
                    NumberAnimation { properties: "x,y"; duration: 100 }
                }
            }

            Menu
            {
                id: contextMenu

                property string key
                property var provider
                property bool settingVisible

                MenuItem
                {
                    //: Settings context menu action
                    text: catalog.i18nc("@action:menu", "Copy value to all extruders")
                    visible: machineExtruderCount.properties.value > 1
                    enabled: contextMenu.provider !== undefined && contextMenu.provider.properties.settable_per_extruder !== "False"
                    onTriggered: Cura.MachineManager.copyValueToExtruders(contextMenu.key)
                }

                MenuItem
                {
                    //: Settings context menu action
                    text: catalog.i18nc("@action:menu", "Copy all changed values to all extruders")
                    visible: machineExtruderCount.properties.value > 1
                    enabled: contextMenu.provider !== undefined
                    onTriggered: Cura.MachineManager.copyAllValuesToExtruders()
                }

                MenuSeparator
                {
                    visible: machineExtruderCount.properties.value > 1
                }

                Instantiator
                {
                    id: customMenuItems
                    model: Cura.SidebarCustomMenuItemsModel { }
                    MenuItem
                    {
                        text: model.name
                        iconName: model.icon_name
                        onTriggered:
                        {
                            customMenuItems.model.callMenuItemMethod(name, model.actions, {"key": contextMenu.key})
                        }
                    }
                   onObjectAdded: contextMenu.insertItem(index, object)
                   onObjectRemoved: contextMenu.removeItem(object)
                }

                MenuSeparator
                {
                    visible: customMenuItems.count > 0
                }

                MenuItem
                {
                    //: Settings context menu action
                    visible: !findingSettings
                    text: catalog.i18nc("@action:menu", "Hide this setting");
                    onTriggered:
                    {
                        definitionsModel.hide(contextMenu.key)
                    }
                }
                MenuItem
                {
                    //: Settings context menu action
                    text:
                    {
                        if (contextMenu.settingVisible)
                        {
                            return catalog.i18nc("@action:menu", "Don't show this setting");
                        }
                        else
                        {
                            return catalog.i18nc("@action:menu", "Keep this setting visible");
                        }
                    }
                    visible: findingSettings
                    onTriggered:
                    {
                        if (contextMenu.settingVisible)
                        {
                            definitionsModel.hide(contextMenu.key);
                        }
                        else
                        {
                            definitionsModel.show(contextMenu.key);
                        }
                    }
                }
                MenuItem
                {
                    //: Settings context menu action
                    text: catalog.i18nc("@action:menu", "Configure setting visibility...");

                    onTriggered: Cura.Actions.configureSettingVisibility.trigger(contextMenu);
                }
            }

            UM.SettingPropertyProvider
            {
                id: machineExtruderCount

                containerStackId: Cura.MachineManager.activeMachine !== null ? Cura.MachineManager.activeMachine.id : ""
                key: "machine_extruder_count"
                watchedProperties: [ "value" ]
                storeIndex: 0
            }
        }
    }
}
