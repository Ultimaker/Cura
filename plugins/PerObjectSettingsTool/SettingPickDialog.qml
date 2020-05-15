import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2

import UM 1.2 as UM
import Cura 1.0 as Cura
import ".."

UM.Dialog
{
    id: settingPickDialog

    title: catalog.i18nc("@title:window", "Select Settings to Customize for this model")
    width: screenScaleFactor * 360

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

    TextField
    {
        id: filterInput

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

    CheckBox
    {
        id: toggleShowAll
        anchors
        {
            top: parent.top
            right: parent.right
        }
        text: catalog.i18nc("@label:checkbox", "Show all")
    }

    ScrollView
    {
        id: scrollView

        anchors
        {
            top: filterInput.bottom
            left: parent.left
            right: parent.right
            bottom: parent.bottom
        }
        ListView
        {
            id: listview
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
            delegate:Loader
            {
                id: loader

                width: parent.width
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
    }

    rightButtons: [
        Button
        {
            text: catalog.i18nc("@action:button", "Close")
            onClicked: settingPickDialog.visible = false
        }
    ]
}