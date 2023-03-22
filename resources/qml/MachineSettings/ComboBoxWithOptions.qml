// Copyright (c) 2020 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.1 as Cura

import "../Widgets"


//
// ComboBox with dropdown options in the Machine Settings dialog.
//
UM.TooltipArea
{
    id: comboBoxWithOptions

    UM.I18nCatalog { id: catalog; name: "cura"; }

    height: childrenRect.height
    width: childrenRect.width
    text: tooltipText

    property int controlWidth: UM.Theme.getSize("setting_control").width
    property int controlHeight: UM.Theme.getSize("setting_control").height

    property alias containerStackId: propertyProvider.containerStackId
    property alias settingKey: propertyProvider.key
    property alias settingStoreIndex: propertyProvider.storeIndex

    property alias labelText: fieldLabel.text
    property alias labelFont: fieldLabel.font
    property alias labelWidth: fieldLabel.width
    property alias optionModel: comboBox.model

    property string tooltipText: propertyProvider.properties.description ? propertyProvider.properties.description : ""

    // callback functions
    property var forceUpdateOnChangeFunction: dummy_func
    property var afterOnEditingFinishedFunction: dummy_func
    property var setValueFunction: null

    // a dummy function for default property values
    function dummy_func() {}

    UM.SettingPropertyProvider
    {
        id: propertyProvider
        watchedProperties: [ "value", "options", "description" ]
    }

    UM.Label
    {
        id: fieldLabel
        anchors.left: parent.left
        anchors.verticalCenter: comboBox.verticalCenter
        visible: text != ""
        font: UM.Theme.getFont("medium")
    }

    ListModel
    {
        id: defaultOptionsModel

        function updateModel() {
            clear();

            if (!propertyProvider.properties.options) {
                return;
            }

            if (typeof(propertyProvider.properties["options"]) === "string") {
                return;
            }

            const keys = propertyProvider.properties["options"].keys();
            for (let index = 0; index < propertyProvider.properties["options"].keys().length; index ++) {
                const key = propertyProvider.properties["options"].keys()[index];
                const value = propertyProvider.properties["options"][key];
                defaultOptionsModel.append({ text: value, value: key });
            }
        }

        Component.onCompleted: updateModel()
    }

    // Remake the model when the model is bound to a different container stack
    Connections
    {
        target: propertyProvider
        function onContainerStackChanged() { defaultOptionsModel.updateModel() }
        function onIsValueUsedChanged() { defaultOptionsModel.updateModel() }
    }

    Cura.ComboBox
    {
        id: comboBox
        anchors.left: fieldLabel.right
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        width: comboBoxWithOptions.controlWidth
        height: comboBoxWithOptions.controlHeight
        model: defaultOptionsModel
        textRole: "text"

        currentIndex: {
            const currentValue = propertyProvider.properties.value
            for (let i = 0; i < model.count; i ++) {
                if (model.get(i).value === currentValue) {
                    return i;
                }
            }
            return -1;
        }

        onActivated: function (index) {
            const newValue = model.get(index).value;

            if (propertyProvider.properties.value !== newValue && newValue !== undefined) {
                if (setValueFunction !== null) {
                    setValueFunction(newValue);
                } else {
                    propertyProvider.setPropertyValue("value", newValue);
                }
                forceUpdateOnChangeFunction();
                afterOnEditingFinishedFunction();
            }
        }
    }
}
