// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// TextField widget with validation for editing numeric data in the Machine Settings dialog.
//
UM.TooltipArea
{
    id: numericTextFieldWithUnit

    UM.I18nCatalog { id: catalog; name: "cura"; }

    height: childrenRect.height
    width: childrenRect.width

    text: tooltipText

    property alias containerStackId: propertyProvider.containerStackId
    property alias settingKey: propertyProvider.key
    property alias settingStoreIndex: propertyProvider.storeIndex

    property alias labelText: fieldLabel.text
    property alias labelWidth: fieldLabel.width
    property alias unitText: unitLabel.text

    property string tooltipText: propertyProvider.properties.description

    // whether negative value is allowed. This affects the validation of the input field.
    property bool allowNegativeValue: false

    // callback functions
    property var afterOnEditingFinishedFunction: dummy_func
    property var forceUpdateOnChangeFunction: dummy_func
    property var setValueFunction: null

    // a dummy function for default property values
    function dummy_func() {}


    UM.SettingPropertyProvider
    {
        id: propertyProvider
        watchedProperties: [ "value", "description" ]
    }

    Row
    {
        id: itemRow
        spacing: UM.Theme.getSize("default_margin").width

        Label
        {
            id: fieldLabel
            anchors.verticalCenter: textFieldWithUnit.verticalCenter
            visible: text != ""
            elide: Text.ElideRight
            renderType: Text.NativeRendering
            //width: Math.max(0, settingsTabs.labelColumnWidth)
        }

        Item
        {
            id: textFieldWithUnit

            width: textField.width
            height: textField.height

            TextField
            {
                id: textField
                text:
                {
                    const value = propertyProvider.properties.value
                    return value ? value : ""
                }
                validator: RegExpValidator { regExp: allowNegativeValue ? /-?[0-9\.,]{0,6}/ : /[0-9\.,]{0,6}/ }
                onEditingFinished:
                {
                    if (propertyProvider && text != propertyProvider.properties.value)
                    {
                        // For some properties like the extruder-compatible material diameter, they need to
                        // trigger many updates, such as the available materials, the current material may
                        // need to be switched, etc. Although setting the diameter can be done directly via
                        // the provider, all the updates that need to be triggered then need to depend on
                        // the metadata update, a signal that can be fired way too often. The update functions
                        // can have if-checks to filter out the irrelevant updates, but still it incurs unnecessary
                        // overhead.
                        // The ExtruderStack class has a dedicated function for this call "setCompatibleMaterialDiameter()",
                        // and it triggers the diameter update signals only when it is needed. Here it is optionally
                        // choose to use setCompatibleMaterialDiameter() or other more specific functions that
                        // are available.
                        if (setValueFunction !== null)
                        {
                            setValueFunction(text)
                        }
                        else
                        {
                            propertyProvider.setPropertyValue("value", text)
                        }
                        forceUpdateOnChangeFunction()
                        afterOnEditingFinished()
                    }
                }
            }

            Label
            {
                id: unitLabel
                anchors.right: textField.right
                anchors.rightMargin: y - textField.y
                anchors.verticalCenter: textField.verticalCenter
                text: unitText
                renderType: Text.NativeRendering
            }
        }
    }
}
