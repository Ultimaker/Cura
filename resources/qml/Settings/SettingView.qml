// Copyright (c) 2017 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

import "../Menus"

Item
{
    id: base;

    property Action configureSettings;
    property bool findingSettings;
    signal showTooltip(Item item, point location, string text);
    signal hideTooltip();

    Item
    {
        id: globalProfileRow
        height: UM.Theme.getSize("sidebar_setup").height
        visible: !sidebar.monitoringPrint && !sidebar.hideSettings

        anchors
        {
            top: parent.top
            left: parent.left
            leftMargin: UM.Theme.getSize("sidebar_margin").width
            right: parent.right
            rightMargin: UM.Theme.getSize("sidebar_margin").width
        }

        Label
        {
            id: globalProfileLabel
            text: catalog.i18nc("@label","Profile:");
            width: Math.floor(parent.width * 0.45 - UM.Theme.getSize("sidebar_margin").width - 2)
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
            verticalAlignment: Text.AlignVCenter
            anchors.top: parent.top
            anchors.bottom: parent.bottom
        }

        ToolButton
        {
            id: globalProfileSelection

            text: {
                var result = Cura.MachineManager.activeQualityName;
                if (Cura.MachineManager.activeQualityLayerHeight > 0) {
                    result += " <font color=\"" + UM.Theme.getColor("text_detail") + "\">";
                    result += " - ";
                    result += Cura.MachineManager.activeQualityLayerHeight + "mm";
                    result += "</font>";
                }
                return result;
            }
            enabled: !header.currentExtruderVisible || header.currentExtruderIndex > -1

            width: Math.floor(parent.width * 0.55)
            height: UM.Theme.getSize("setting_control").height
            anchors.left: globalProfileLabel.right
            anchors.right: parent.right
            tooltip: Cura.MachineManager.activeQualityName
            style: UM.Theme.styles.sidebar_header_button
            activeFocusOnPress: true;
            menu: ProfileMenu { }

            UM.SimpleButton
            {
                id: customisedSettings

                visible: Cura.MachineManager.hasUserSettings
                height: Math.floor(parent.height * 0.6)
                width: Math.floor(parent.height * 0.6)

                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                anchors.rightMargin: UM.Theme.getSize("setting_preferences_button_margin").width - UM.Theme.getSize("sidebar_margin").width

                color: hovered ? UM.Theme.getColor("setting_control_button_hover") : UM.Theme.getColor("setting_control_button");
                iconSource: UM.Theme.getIcon("star");

                onClicked:
                {
                    forceActiveFocus();
                    Cura.Actions.manageProfiles.trigger()
                }
                onEntered:
                {
                    var content = catalog.i18nc("@tooltip","Some setting/override values are different from the values stored in the profile.\n\nClick to open the profile manager.")
                    base.showTooltip(globalProfileRow, Qt.point(-UM.Theme.getSize("sidebar_margin").width, 0),  content)
                }
                onExited: base.hideTooltip()
            }
        }
    }

    Rectangle
    {
        id: filterContainer
        visible: true

        border.width: UM.Theme.getSize("default_lining").width
        border.color:
        {
            if(hoverMouseArea.containsMouse || clearFilterButton.containsMouse)
            {
                return UM.Theme.getColor("setting_control_border_highlight");
            }
            else
            {
                return UM.Theme.getColor("setting_control_border");
            }
        }

        color: UM.Theme.getColor("setting_control")

        anchors
        {
            top: globalProfileRow.bottom
            topMargin: UM.Theme.getSize("sidebar_margin").height
            left: parent.left
            leftMargin: UM.Theme.getSize("sidebar_margin").width
            right: parent.right
            rightMargin: UM.Theme.getSize("sidebar_margin").width
        }
        height: visible ? UM.Theme.getSize("setting_control").height : 0
        Behavior on height { NumberAnimation { duration: 100 } }

        TextField
        {
            id: filter;

            anchors.left: parent.left
            anchors.right: clearFilterButton.left
            anchors.rightMargin: UM.Theme.getSize("sidebar_margin").width

            placeholderText: catalog.i18nc("@label:textbox", "Search...")

            style: TextFieldStyle
            {
                textColor: UM.Theme.getColor("setting_control_text");
                placeholderTextColor: UM.Theme.getColor("setting_control_text")
                font: UM.Theme.getFont("default");
                background: Item {}
            }

            property var expandedCategories
            property bool lastFindingSettings: false

            onTextChanged:
            {
                definitionsModel.filter = {"i18n_label": "*" + text};
                findingSettings = (text.length > 0);
                if(findingSettings != lastFindingSettings)
                {
                    if(findingSettings)
                    {
                        expandedCategories = definitionsModel.expanded.slice();
                        definitionsModel.expanded = ["*"];
                        definitionsModel.showAncestors = true;
                        definitionsModel.showAll = true;
                    }
                    else
                    {
                        definitionsModel.expanded = expandedCategories;
                        definitionsModel.showAncestors = false;
                        definitionsModel.showAll = false;
                    }
                    lastFindingSettings = findingSettings;
                }
            }

            Keys.onEscapePressed:
            {
                filter.text = "";
            }
        }

        MouseArea
        {
            id: hoverMouseArea
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.NoButton
            cursorShape: Qt.IBeamCursor
        }

        UM.SimpleButton
        {
            id: clearFilterButton
            iconSource: UM.Theme.getIcon("cross1")
            visible: findingSettings

            height: parent.height * 0.4
            width: visible ? height : 0

            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("sidebar_margin").width

            color: UM.Theme.getColor("setting_control_button")
            hoverColor: UM.Theme.getColor("setting_control_button_hover")

            onClicked:
            {
                filter.text = "";
                filter.forceActiveFocus();
            }
        }
    }

    ScrollView
    {
        anchors.top: filterContainer.bottom;
        anchors.bottom: parent.bottom;
        anchors.right: parent.right;
        anchors.left: parent.left;
        anchors.topMargin: filterContainer.visible ? UM.Theme.getSize("sidebar_margin").height : 0
        Behavior on anchors.topMargin { NumberAnimation { duration: 100 } }

        style: UM.Theme.styles.scrollview;
        flickableItem.flickableDirection: Flickable.VerticalFlick;
        __wheelAreaScrollSpeed: 75; // Scroll three lines in one scroll event

        ListView
        {
            id: contents
            spacing: UM.Theme.getSize("default_lining").height;
            cacheBuffer: 1000000;   // Set a large cache to effectively just cache every list item.

            model: UM.SettingDefinitionsModel
            {
                id: definitionsModel;
                containerId: Cura.MachineManager.activeDefinitionId
                visibilityHandler: UM.SettingPreferenceVisibilityHandler { }
                exclude: ["machine_settings", "command_line_settings", "infill_mesh", "infill_mesh_order", "cutting_mesh", "support_mesh", "anti_overhang_mesh"] // TODO: infill_mesh settigns are excluded hardcoded, but should be based on the fact that settable_globally, settable_per_meshgroup and settable_per_extruder are false.
                expanded: CuraApplication.expandedCategories
                onExpandedChanged:
                {
                    if(!findingSettings)
                    {
                        // Do not change expandedCategories preference while filtering settings
                        // because all categories are expanded while filtering
                        CuraApplication.setExpandedCategories(expanded)
                    }
                }
                onVisibilityChanged: Cura.SettingInheritanceManager.forceUpdate()
            }

            property var indexWithFocus: -1

            delegate: Loader
            {
                id: delegate

                width: UM.Theme.getSize("sidebar").width;
                height: provider.properties.enabled == "True" ? UM.Theme.getSize("section").height : - contents.spacing
                Behavior on height { NumberAnimation { duration: 100 } }
                opacity: provider.properties.enabled == "True" ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: 100 } }
                enabled:
                {
                    if(!ExtruderManager.activeExtruderStackId && machineExtruderCount.properties.value > 1)
                    {
                        // disable all controls on the global tab, except categories
                        return model.type == "category"
                    }
                    return provider.properties.enabled == "True"
                }

                property var definition: model
                property var settingDefinitionsModel: definitionsModel
                property var propertyProvider: provider
                property var globalPropertyProvider: inheritStackProvider

                //Qt5.4.2 and earlier has a bug where this causes a crash: https://bugreports.qt.io/browse/QTBUG-35989
                //In addition, while it works for 5.5 and higher, the ordering of the actual combo box drop down changes,
                //causing nasty issues when selecting different options. So disable asynchronous loading of enum type completely.
                asynchronous: model.type != "enum" && model.type != "extruder" && model.type != "optional_extruder"
                active: model.type != undefined

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
                    when: model.settable_per_extruder || (inheritStackProvider.properties.limit_to_extruder != null && inheritStackProvider.properties.limit_to_extruder >= 0);
                    value:
                    {
                        // associate this binding with Cura.MachineManager.activeMachineId in the beginning so this
                        // binding will be triggered when activeMachineId is changed too.
                        // Otherwise, if this value only depends on the extruderIds, it won't get updated when the
                        // machine gets changed.
                        var activeMachineId = Cura.MachineManager.activeMachineId;

                        if(!model.settable_per_extruder || machineExtruderCount.properties.value == 1)
                        {
                            //Not settable per extruder or there only is global, so we must pick global.
                            return activeMachineId;
                        }
                        if(inheritStackProvider.properties.limit_to_extruder != null && inheritStackProvider.properties.limit_to_extruder >= 0)
                        {
                            //We have limit_to_extruder, so pick that stack.
                            return ExtruderManager.extruderIds[String(inheritStackProvider.properties.limit_to_extruder)];
                        }
                        if(ExtruderManager.activeExtruderStackId)
                        {
                            //We're on an extruder tab. Pick the current extruder.
                            return ExtruderManager.activeExtruderStackId;
                        }
                        //No extruder tab is selected. Pick the global stack. Shouldn't happen any more since we removed the global tab.
                        return activeMachineId;
                    }
                }

                // Specialty provider that only watches global_inherits (we cant filter on what property changed we get events
                // so we bypass that to make a dedicated provider).
                UM.SettingPropertyProvider
                {
                    id: inheritStackProvider
                    containerStackId: Cura.MachineManager.activeMachineId
                    key: model.key
                    watchedProperties: [ "limit_to_extruder" ]
                }

                UM.SettingPropertyProvider
                {
                    id: provider

                    containerStackId: Cura.MachineManager.activeMachineId
                    key: model.key ? model.key : ""
                    watchedProperties: [ "value", "enabled", "state", "validationState", "settable_per_extruder", "resolve" ]
                    storeIndex: 0
                    // Due to the way setPropertyValue works, removeUnusedValue gives the correct output in case of resolve
                    removeUnusedValue: model.resolve == undefined
                }

                Connections
                {
                    target: item
                    onContextMenuRequested:
                    {
                        contextMenu.key = model.key;
                        contextMenu.settingVisible = model.visible;
                        contextMenu.provider = provider
                        contextMenu.popup();
                    }
                    onShowTooltip: base.showTooltip(delegate, { x: -UM.Theme.getSize("default_arrow").width, y: delegate.height / 2 }, text)
                    onHideTooltip: base.hideTooltip()
                    onShowAllHiddenInheritedSettings:
                    {
                        var children_with_override = Cura.SettingInheritanceManager.getChildrenKeysWithOverride(category_id)
                        for(var i = 0; i < children_with_override.length; i++)
                        {
                            definitionsModel.setVisible(children_with_override[i], true)
                        }
                        Cura.SettingInheritanceManager.manualRemoveOverride(category_id)
                    }
                    onFocusReceived:
                    {
                        contents.indexWithFocus = index;
                        animateContentY.from = contents.contentY;
                        contents.positionViewAtIndex(index, ListView.Contain);
                        animateContentY.to = contents.contentY;
                        animateContentY.running = true;
                    }
                    onSetActiveFocusToNextSetting:
                    {
                        if(forward == undefined || forward)
                        {
                            contents.currentIndex = contents.indexWithFocus + 1;
                            while(contents.currentItem && contents.currentItem.height <= 0)
                            {
                                contents.currentIndex++;
                            }
                            if(contents.currentItem)
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
                            if(contents.currentItem)
                            {
                                contents.currentItem.item.focusItem.forceActiveFocus();
                            }
                        }
                    }
                }
            }

            UM.I18nCatalog { id: catalog; name: "cura"; }

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
                    enabled: contextMenu.provider != undefined && contextMenu.provider.properties.settable_per_extruder != "False"
                    onTriggered: Cura.MachineManager.copyValueToExtruders(contextMenu.key)
                }

                MenuSeparator
                {
                    visible: machineExtruderCount.properties.value > 1
                }

                MenuItem
                {
                    //: Settings context menu action
                    visible: !findingSettings;
                    text: catalog.i18nc("@action:menu", "Hide this setting");
                    onTriggered: definitionsModel.hide(contextMenu.key);
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
                    visible: findingSettings;
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
                    text: catalog.i18nc("@action:menu", "Configure setting visiblity...");

                    onTriggered: Cura.Actions.configureSettingVisibility.trigger(contextMenu);
                }
            }

            UM.SettingPropertyProvider
            {
                id: machineExtruderCount

                containerStackId: Cura.MachineManager.activeMachineId
                key: "machine_extruder_count"
                watchedProperties: [ "value" ]
                storeIndex: 0
            }
        }
    }
}