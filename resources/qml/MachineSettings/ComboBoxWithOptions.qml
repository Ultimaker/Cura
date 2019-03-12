// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// ComboBox with dropdown options in the Machine Settings dialog.
//
UM.TooltipArea
{
    id: comboBoxWithOptions

    UM.I18nCatalog { id: catalog; name: "cura"; }

    height: childrenRect.height
    width: childrenRect.width
    text: tooltip

    property alias containerStackId: propertyProvider.containerStackId
    property alias settingKey: propertyProvider.key
    property alias settingStoreIndex: propertyProvider.storeIndex

    property alias labelText: fieldLabel.text
    property alias labelWidth: fieldLabel.width

    property string tooltip: propertyProvider.properties.description

    // callback functions
    property var afterOnActivateFunction: dummy_func
    property var forceUpdateOnChangeFunction: dummy_func

    // a dummy function for default property values
    function dummy_func() {}

    UM.SettingPropertyProvider
    {
        id: propertyProvider
        watchedProperties: [ "value", "options", "description" ]
    }

    Row
    {
        spacing: UM.Theme.getSize("default_margin").width

        Label
        {
            id: fieldLabel
            anchors.verticalCenter: comboBox.verticalCenter
            visible: text != ""
            elide: Text.ElideRight
            //width: Math.max(0, settingsTabs.labelColumnWidth)
        }
        ComboBox
        {
            id: comboBox
            model: ListModel
            {
                id: optionsModel
                Component.onCompleted:
                {
                    // Options come in as a string-representation of an OrderedDict
                    var options = propertyProvider.properties.options.match(/^OrderedDict\(\[\((.*)\)\]\)$/)
                    if (options)
                    {
                        options = options[1].split("), (")
                        for (var i = 0; i < options.length; i++)
                        {
                            var option = options[i].substring(1, options[i].length - 1).split("', '")
                            optionsModel.append({text: option[1], value: option[0]});
                        }
                    }
                }
            }
            currentIndex:
            {
                var currentValue = propertyProvider.properties.value
                var index = 0
                for (var i = 0; i < optionsModel.count; i++)
                {
                    if (optionsModel.get(i).value == currentValue)
                    {
                        index = i
                        break
                    }
                }
                return index
            }
            onActivated:
            {
                if(propertyProvider.properties.value != optionsModel.get(index).value)
                {
                    propertyProvider.setPropertyValue("value", optionsModel.get(index).value);
                    forceUpdateOnChangeFunction()
                    afterOnActivateFunction()
                }
            }
        }
    }
}
