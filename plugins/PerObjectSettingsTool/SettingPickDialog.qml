//Copyright (c) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.2

import UM 1.5 as UM
import Cura 1.0 as Cura
import ".."

UM.Dialog
{
    id: settingPickDialog

    title: catalog.i18nc("@title:window", "Select Settings to Customize for this model")
    width: UM.Theme.getSize("small_popup_dialog").width
    backgroundColor: UM.Theme.getColor("background_1")

    property var additional_excluded_settings

    onVisibilityChanged:
    {
        // force updating the model to sync it with addedSettingsModel
        if (visible)
        {
            listview.model.forceUpdate()
            updateFilter()
        }
    }

    function updateFilter()
    {
        var new_filter = {}
        new_filter["settable_per_mesh"] = true
        // Don't filter on "settable_per_meshgroup" any more when `printSequencePropertyProvider.properties.value`
        //   is set to "one_at_a_time", because the current backend architecture isn't ready for that.

        if (filterInput.text != "")
        {
            new_filter["i18n_label"] = "*" + filterInput.text
        }

        listview.model.filter = new_filter
    }

    Cura.TextField
    {
        id: filterInput
        selectByMouse: true

        anchors
        {
            top: parent.top
            left: parent.left
            right: toggleShowAll.left
            rightMargin: UM.Theme.getSize("default_margin").width
        }

        placeholderText: catalog.i18nc("@label:textbox", "Filter...")

        onTextChanged: settingPickDialog.updateFilter()
    }

    UM.CheckBox
    {
        id: toggleShowAll
        anchors
        {
            top: parent.top
            right: parent.right
            verticalCenter: filterInput.verticalCenter
        }
        text: catalog.i18nc("@label:checkbox", "Show all")
    }

    ListView
    {
        id: listview
        anchors
        {
            top: filterInput.bottom
            topMargin: UM.Theme.getSize("default_margin").height
            left: parent.left
            right: parent.right
            bottom: parent.bottom
        }

        ScrollBar.vertical: UM.ScrollBar { id: scrollBar }
        clip: true

        model: UM.SettingDefinitionsModel
        {
            id: definitionsModel
            containerId: Cura.MachineManager.activeMachine != null ? Cura.MachineManager.activeMachine.definition.id: ""
            visibilityHandler: UM.SettingPreferenceVisibilityHandler {}
            expanded: [ "*" ]
            exclude:
            {
                var excluded_settings = [ "machine_settings", "command_line_settings", "support_mesh", "anti_overhang_mesh", "cutting_mesh", "infill_mesh" ]
                excluded_settings = excluded_settings.concat(settingPickDialog.additional_excluded_settings)
                return excluded_settings
            }
            showAll: toggleShowAll.checked || filterInput.text !== ""
        }
        delegate: Loader
        {
            id: loader

            width: listview.width - scrollBar.width
            height: model.type != undefined ? UM.Theme.getSize("section").height : 0

            property var definition: model
            property var settingDefinitionsModel: definitionsModel

            asynchronous: true
            source:
            {
                switch(model.type)
                {
                    case "category":
                        return "PerObjectCategory.qml"
                    default:
                        return "PerObjectItem.qml"
                }
            }
        }
        Component.onCompleted: settingPickDialog.updateFilter()
    }

    rightButtons: [
        Cura.TertiaryButton
        {
            text: catalog.i18nc("@action:button", "Close")
            onClicked: reject()
        }
    ]
}