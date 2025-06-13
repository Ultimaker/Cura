// Copyright (c) 2022 Jaime van Kessel, Ultimaker B.V.
// The PostProcessingPlugin is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.15
import QtQml.Models 2.15 as Models
import QtQuick.Layouts 1.1
import QtQuick.Window 2.2

import UM 1.5 as UM
import Cura 1.0 as Cura

UM.Dialog
{
    id: dialog

    title: catalog.i18nc("@title:window", "Post Processing Plugin")
    width: 700 * screenScaleFactor
    height: 500 * screenScaleFactor
    minimumWidth: 400 * screenScaleFactor
    minimumHeight: 250 * screenScaleFactor
    backgroundColor: UM.Theme.getColor("main_background")
    onVisibleChanged:
    {
        // Whenever the window is closed (either via the "Close" button or the X on the window frame), we want to update it in the stack.
        if (!visible)
        {
            manager.writeScriptsToStack()
        }
    }

    Item
    {
        UM.I18nCatalog{id: catalog; name: "cura"}
        id: base
        property int columnWidth: Math.round((base.width / 2) - UM.Theme.getSize("default_margin").width)
        property int textMargin: UM.Theme.getSize("narrow_margin").width
        property string activeScriptName

        anchors.fill: parent

        ButtonGroup
        {
            id: selectedScriptGroup
        }
        Column
        {
            id: activeScripts
            width: base.columnWidth
            height: parent.height

            spacing: base.textMargin

            UM.Label
            {
                id: activeScriptsHeader
                text: catalog.i18nc("@label", "Post Processing Scripts")
                anchors.left: parent.left
                anchors.right: parent.right
                font: UM.Theme.getFont("large_bold")
                elide: Text.ElideRight
            }
            ListView
            {
                id: activeScriptsList
                anchors
                {
                    left: parent.left
                    right: parent.right
                    rightMargin: base.textMargin
                }
                height: Math.min(contentHeight, parent.height - parent.spacing * 2 - activeScriptsHeader.height - addButton.height) //At the window height, start scrolling this one.

                clip: true
                ScrollBar.vertical: UM.ScrollBar
                {
                    id: activeScriptsScrollBar
                }
                model: manager.scriptList

                delegate: Button
                {
                    id: activeScriptButton

                    width: parent.width - activeScriptsScrollBar.width
                    height: UM.Theme.getSize("standard_list_lineheight").height

                    ButtonGroup.group: selectedScriptGroup
                    checkable: true

                    checked:
                    {
                        if (manager.selectedScriptIndex == index)
                        {
                            base.activeScriptName = manager.getScriptLabelByKey(modelData.toString())
                            return true
                        }
                        else
                        {
                            return false
                        }
                    }

                    background: Rectangle
                    {
                        color: activeScriptButton.checked ? UM.Theme.getColor("background_3") : "transparent"
                    }

                    onClicked:
                    {
                        forceActiveFocus()
                        manager.setSelectedScriptIndex(index)
                        base.activeScriptName = manager.getScriptLabelByKey(modelData.toString())
                    }

                    RowLayout
                    {
                        anchors.fill: parent

                        UM.Label
                        {
                            Layout.fillWidth: true
                            Layout.preferredHeight: height
                            elide: Text.ElideRight
                            text: manager.getScriptLabelByKey(modelData.toString())
                        }

                        Item
                        {
                            id: downButton
                            Layout.preferredWidth: height
                            Layout.fillHeight: true
                            enabled: index != manager.scriptList.length - 1

                            MouseArea
                            {
                                anchors.fill: parent
                                onClicked:
                                {
                                    if (manager.selectedScriptIndex == index)
                                    {
                                        manager.setSelectedScriptIndex(index + 1)
                                    }
                                    return manager.moveScript(index, index + 1)
                                }
                            }

                            UM.ColorImage
                            {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.horizontalCenter: parent.horizontalCenter
                                width: UM.Theme.getSize("standard_arrow").width
                                height: UM.Theme.getSize("standard_arrow").height
                                color: parent.enabled ? UM.Theme.getColor("text") : UM.Theme.getColor("text_disabled")
                                source: UM.Theme.getIcon("ChevronSingleDown")
                            }
                        }
                        Item
                        {
                            id: upButton
                            Layout.preferredWidth: height
                            Layout.fillHeight: true
                            enabled: index != 0

                            MouseArea
                            {
                                anchors.fill: parent
                                onClicked:
                                {
                                    if (manager.selectedScriptIndex == index)
                                    {
                                        manager.setSelectedScriptIndex(index - 1)
                                    }
                                    return manager.moveScript(index, index - 1)
                                }
                            }

                            UM.ColorImage
                            {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.horizontalCenter: parent.horizontalCenter
                                width: UM.Theme.getSize("standard_arrow").width
                                height: UM.Theme.getSize("standard_arrow").height
                                color: upButton.enabled ? UM.Theme.getColor("text") : UM.Theme.getColor("text_disabled")
                                source: UM.Theme.getIcon("ChevronSingleUp")
                            }
                        }

                        Item
                        {
                            id: removeButton
                            Layout.preferredWidth: height
                            Layout.fillHeight: true

                            MouseArea
                            {
                                anchors.fill: parent
                                onClicked: manager.removeScriptByIndex(index)
                            }

                            UM.ColorImage
                            {
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.horizontalCenter: parent.horizontalCenter
                                width: UM.Theme.getSize("standard_arrow").width
                                height: UM.Theme.getSize("standard_arrow").height
                                color: UM.Theme.getColor("text")
                                source: UM.Theme.getIcon("Cancel")
                            }
                        }
                    }
                }
            }
            Cura.SecondaryButton
            {
                id: addButton
                text: catalog.i18nc("@action", "Add a script")
                onClicked: scriptsMenu.open()
            }
        }

        Cura.Menu
        {
            id: scriptsMenu

            Models.Instantiator
            {
                model: manager.loadedScriptList

                Cura.MenuItem
                {
                    text: manager.getScriptLabelByKey(modelData.toString())
                    onTriggered: manager.addScriptToList(modelData.toString())
                }

                onObjectAdded: function(index, object) { scriptsMenu.insertItem(index, object)}
                onObjectRemoved: function(index, object) {  scriptsMenu.removeItem(object) }
            }
        }

        Rectangle
        {
            color: UM.Theme.getColor("main_background")
            anchors.left: activeScripts.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.right: parent.right
            height: parent.height
            id: settingsPanel

            UM.Label
            {
                id: scriptSpecsHeader
                text: manager.selectedScriptIndex == -1 ? catalog.i18nc("@label", "Settings") : base.activeScriptName
                anchors
                {
                    top: parent.top
                    topMargin: base.textMargin
                    left: parent.left
                    leftMargin: base.textMargin
                    right: parent.right
                    rightMargin: base.textMargin
                }

                elide: Text.ElideRight
                height: 20 * screenScaleFactor
                font: UM.Theme.getFont("large_bold")
            }

            ListView
            {
                id: listview
                anchors
                {
                    top: scriptSpecsHeader.bottom
                    topMargin: settingsPanel.textMargin
                    left: parent.left
                    leftMargin: UM.Theme.getSize("default_margin").width
                    right: parent.right
                    bottom: parent.bottom
                }

                ScrollBar.vertical: UM.ScrollBar {}
                clip: true
                visible: manager.selectedScriptDefinitionId != ""
                spacing: UM.Theme.getSize("default_lining").height

                model: UM.SettingDefinitionsModel
                {
                    id: definitionsModel
                    containerId: manager.selectedScriptDefinitionId
                    onContainerIdChanged: definitionsModel.setAllVisible(true)
                    showAll: true
                }

                delegate: Loader
                {
                    id: settingLoader

                    width: listview.width
                    height:
                    {
                        if (provider.properties.enabled == "True" && model.type != undefined)
                        {
                            return UM.Theme.getSize("section").height;
                        }
                        else
                        {
                            return 0
                        }
                    }
                    Behavior on height { NumberAnimation { duration: 100 } }
                    opacity: provider.properties.enabled == "True" ? 1 : 0

                    Behavior on opacity { NumberAnimation { duration: 100 } }
                    enabled: opacity > 0

                    property var definition: model
                    property var settingDefinitionsModel: definitionsModel
                    property var propertyProvider: provider
                    property var globalPropertyProvider: inheritStackProvider

                    //Qt5.4.2 and earlier has a bug where this causes a crash: https://bugreports.qt.io/browse/QTBUG-35989
                    //In addition, while it works for 5.5 and higher, the ordering of the actual combo box drop down changes,
                    //causing nasty issues when selecting different options. So disable asynchronous loading of enum type completely.
                    asynchronous: model.type != "enum" && model.type != "extruder"

                    onLoaded:
                    {
                        settingLoader.item.showRevertButton = false
                        settingLoader.item.showInheritButton = false
                        settingLoader.item.showLinkedSettingIcon = false
                        settingLoader.item.doDepthIndentation = false
                        settingLoader.item.doQualityUserSettingEmphasis = false
                    }

                    sourceComponent:
                    {
                        switch(model.type)
                        {
                            case "int":
                                return settingTextField
                            case "float":
                                return settingTextField
                            case "enum":
                                return settingComboBox
                            case "extruder":
                                return settingExtruder
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

                    UM.SettingPropertyProvider
                    {
                        id: provider
                        containerStackId: manager.selectedScriptStackId
                        key: model.key ? model.key : "None"
                        watchedProperties: [ "value", "enabled", "state", "validationState" ]
                        storeIndex: 0
                    }

                    // Specialty provider that only watches global_inherits (we can't filter on what property changed we get events
                    // so we bypass that to make a dedicated provider).
                    UM.SettingPropertyProvider
                    {
                        id: inheritStackProvider
                        containerStack: Cura.MachineManager.activeMachine
                        key: model.key ? model.key : "None"
                        watchedProperties: [ "limit_to_extruder" ]
                    }

                    Connections
                    {
                        target: item

                        function onShowTooltip(text)
                        {
                            tooltip.text = text;
                            var position = settingLoader.mapToItem(settingsPanel, settingsPanel.x, 0);
                            tooltip.show(position);
                            tooltip.target.x = position.x + 1;
                        }

                        function onHideTooltip() { tooltip.hide() }
                    }
                }
            }
        }

        Cura.PrintSetupTooltip
        {
            id: tooltip
        }

        Component
        {
            id: settingTextField;

            Cura.SettingTextField { }
        }

        Component
        {
            id: settingComboBox;

            Cura.SettingComboBox { }
        }

        Component
        {
            id: settingExtruder;

            Cura.SettingExtruder { }
        }

        Component
        {
            id: settingCheckBox;

            Cura.SettingCheckBox { }
        }

        Component
        {
            id: settingCategory;

            Cura.SettingCategory { }
        }

        Component
        {
            id: settingUnknown;

            Cura.SettingUnknown { }
        }
    }

    rightButtons: Cura.TertiaryButton
    {
        text: catalog.i18nc("@action:button", "Close")
        onClicked: dialog.accept()
    }

    Item
    {
        objectName: "postProcessingSaveAreaButton"
        visible: activeScriptsList.count > 0
        height: UM.Theme.getSize("action_button").height
        width: height

        Cura.SecondaryButton
        {
            height: UM.Theme.getSize("action_button").height
            tooltip:
            {
                var tipText = catalog.i18nc("@info:tooltip", "Change active post-processing scripts.");
                if (activeScriptsList.count > 0)
                {
                    tipText += "<br><br>" + catalog.i18ncp("@info:tooltip",
                        "The following script is active:",
                        "The following scripts are active:",
                        activeScriptsList.count
                    ) + "<ul>";
                    for(var i = 0; i < activeScriptsList.count; i++)
                    {
                        tipText += "<li>" + manager.getScriptLabelByKey(manager.scriptList[i]) + "</li>";
                    }
                    tipText += "</ul>";
                }
                return tipText
            }
            toolTipContentAlignment: UM.Enums.ContentAlignment.AlignLeft
            onClicked: dialog.show()
            iconSource: Qt.resolvedUrl("Script.svg")
            fixedWidthMode: false
        }

        Cura.NotificationIcon
        {
            id: activeScriptCountIcon
            visible: activeScriptsList.count > 0
            anchors
            {
                horizontalCenter: parent.right
                verticalCenter: parent.top
            }

            labelText: activeScriptsList.count
        }
    }
}
