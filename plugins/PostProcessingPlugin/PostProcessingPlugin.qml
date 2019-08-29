// Copyright (c) 2015 Jaime van Kessel, Ultimaker B.V.
// The PostProcessingPlugin is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2

import UM 1.2 as UM
import Cura 1.0 as Cura

UM.Dialog
{
    id: dialog

    title: catalog.i18nc("@title:window", "Post Processing Plugin")
    width: 700 * screenScaleFactor;
    height: 500 * screenScaleFactor;
    minimumWidth: 400 * screenScaleFactor;
    minimumHeight: 250 * screenScaleFactor;

    onVisibleChanged:
    {
        if(!visible) //Whenever the window is closed (either via the "Close" button or the X on the window frame), we want to update it in the stack.
        {
            manager.writeScriptsToStack()
        }
    }

    Item
    {
        UM.I18nCatalog{id: catalog; name: "cura"}
        id: base
        property int columnWidth: Math.round((base.width / 2) - UM.Theme.getSize("default_margin").width)
        property int textMargin: Math.round(UM.Theme.getSize("default_margin").width / 2)
        property string activeScriptName
        SystemPalette{ id: palette }
        SystemPalette{ id: disabledPalette; colorGroup: SystemPalette.Disabled }
        anchors.fill: parent

        ExclusiveGroup
        {
            id: selectedScriptGroup
        }
        Item
        {
            id: activeScripts
            anchors.left: parent.left
            width: base.columnWidth
            height: parent.height

            Label
            {
                id: activeScriptsHeader
                text: catalog.i18nc("@label", "Post Processing Scripts")
                anchors.top: parent.top
                anchors.topMargin: base.textMargin
                anchors.left: parent.left
                anchors.leftMargin: base.textMargin
                anchors.right: parent.right
                anchors.rightMargin: base.textMargin
                font: UM.Theme.getFont("large_bold")
                elide: Text.ElideRight
            }
            ListView
            {
                id: activeScriptsList

                anchors
                {
                    top: activeScriptsHeader.bottom
                    left: parent.left
                    right: parent.right
                    rightMargin: base.textMargin
                    topMargin: base.textMargin
                    leftMargin: UM.Theme.getSize("default_margin").width
                }

                height: childrenRect.height
                model: manager.scriptList
                delegate: Item
                {
                    width: parent.width
                    height: activeScriptButton.height
                    Button
                    {
                        id: activeScriptButton
                        text: manager.getScriptLabelByKey(modelData.toString())
                        exclusiveGroup: selectedScriptGroup
                        width: parent.width
                        height: UM.Theme.getSize("setting").height
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
                        onClicked:
                        {
                            forceActiveFocus()
                            manager.setSelectedScriptIndex(index)
                            base.activeScriptName = manager.getScriptLabelByKey(modelData.toString())
                        }

                        style: ButtonStyle
                        {
                            background: Rectangle
                            {
                                color: activeScriptButton.checked ? palette.highlight : "transparent"
                                width: parent.width
                                height: parent.height
                            }
                            label: Label
                            {
                                wrapMode: Text.Wrap
                                text: control.text
                                elide: Text.ElideRight
                                color: activeScriptButton.checked ? palette.highlightedText : palette.text
                            }
                        }
                    }

                    Button
                    {
                        id: removeButton
                        text: "x"
                        width: 20 * screenScaleFactor
                        height: 20 * screenScaleFactor
                        anchors.right:parent.right
                        anchors.rightMargin: base.textMargin
                        anchors.verticalCenter: parent.verticalCenter
                        onClicked: manager.removeScriptByIndex(index)
                        style: ButtonStyle
                        {
                            label: Item
                            {
                                UM.RecolorImage
                                {
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    width: Math.round(control.width / 2.7)
                                    height: Math.round(control.height / 2.7)
                                    sourceSize.height: width
                                    color: palette.text
                                    source: UM.Theme.getIcon("cross1")
                                }
                            }
                        }
                    }
                    Button
                    {
                        id: downButton
                        text: ""
                        anchors.right: removeButton.left
                        anchors.verticalCenter: parent.verticalCenter
                        enabled: index != manager.scriptList.length - 1
                        width: 20 * screenScaleFactor
                        height: 20 * screenScaleFactor
                        onClicked:
                        {
                            if (manager.selectedScriptIndex == index)
                            {
                                manager.setSelectedScriptIndex(index + 1)
                            }
                            return manager.moveScript(index, index + 1)
                        }
                        style: ButtonStyle
                        {
                            label: Item
                            {
                                UM.RecolorImage
                                {
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    width: Math.round(control.width / 2.5)
                                    height: Math.round(control.height / 2.5)
                                    sourceSize.height: width
                                    color: control.enabled ? palette.text : disabledPalette.text
                                    source: UM.Theme.getIcon("arrow_bottom")
                                }
                            }
                        }
                    }
                    Button
                    {
                        id: upButton
                        text: ""
                        enabled: index != 0
                        width: 20 * screenScaleFactor
                        height: 20 * screenScaleFactor
                        anchors.right: downButton.left
                        anchors.verticalCenter: parent.verticalCenter
                        onClicked:
                        {
                            if (manager.selectedScriptIndex == index)
                            {
                                manager.setSelectedScriptIndex(index - 1)
                            }
                            return manager.moveScript(index, index - 1)
                        }
                        style: ButtonStyle
                        {
                            label: Item
                             {
                                UM.RecolorImage
                                {
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    width: Math.round(control.width / 2.5)
                                    height: Math.round(control.height / 2.5)
                                    sourceSize.height: width
                                    color: control.enabled ? palette.text : disabledPalette.text
                                    source: UM.Theme.getIcon("arrow_top")
                                }
                            }
                        }
                    }
                }
            }
            Button
            {
                id: addButton
                text: catalog.i18nc("@action", "Add a script")
                anchors.left: parent.left
                anchors.leftMargin: base.textMargin
                anchors.top: activeScriptsList.bottom
                anchors.topMargin: base.textMargin
                menu: scriptsMenu
                style: ButtonStyle
                {
                    label: Label
                    {
                        text: control.text
                    }
                }
            }
            Menu
            {
                id: scriptsMenu

                Instantiator
                {
                    model: manager.loadedScriptList

                    MenuItem
                    {
                        text: manager.getScriptLabelByKey(modelData.toString())
                        onTriggered: manager.addScriptToList(modelData.toString())
                    }

                    onObjectAdded: scriptsMenu.insertItem(index, object)
                    onObjectRemoved: scriptsMenu.removeItem(object)
                }
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

            Label
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
                color: UM.Theme.getColor("text")
            }

            ScrollView
            {
                id: scrollView
                anchors
                {
                    top: scriptSpecsHeader.bottom
                    topMargin: settingsPanel.textMargin
                    left: parent.left
                    leftMargin: UM.Theme.getSize("default_margin").width
                    right: parent.right
                    bottom: parent.bottom
                }

                visible: manager.selectedScriptDefinitionId != ""
                style: UM.Theme.styles.scrollview;

                ListView
                {
                    id: listview
                    spacing: UM.Theme.getSize("default_lining").height
                    model: UM.SettingDefinitionsModel
                    {
                        id: definitionsModel
                        containerId: manager.selectedScriptDefinitionId
                        showAll: true
                    }

                    delegate: Loader
                    {
                        id: settingLoader

                        width: parent.width
                        height:
                        {
                            if(provider.properties.enabled == "True")
                            {
                                if(model.type != undefined)
                                {
                                    return UM.Theme.getSize("section").height
                                }
                                else
                                {
                                    return 0
                                }
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

                        // Specialty provider that only watches global_inherits (we cant filter on what property changed we get events
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

                            onShowTooltip:
                            {
                                tooltip.text = text
                                var position = settingLoader.mapToItem(settingsPanel, settingsPanel.x, 0)
                                tooltip.show(position)
                                tooltip.target.x = position.x + 1
                            }

                            onHideTooltip: tooltip.hide()
                        }
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

    rightButtons: Button
    {
        text: catalog.i18nc("@action:button", "Close")
        iconName: "dialog-close"
        onClicked: dialog.accept()
    }

    Cura.SecondaryButton
    {
        objectName: "postProcessingSaveAreaButton"
        visible: activeScriptsList.count > 0
        height: UM.Theme.getSize("action_button").height
        width: height
        tooltip: catalog.i18nc("@info:tooltip", "Change active post-processing scripts")
        onClicked: dialog.show()
        iconSource: "postprocessing.svg"
        fixedWidthMode: true
    }
}