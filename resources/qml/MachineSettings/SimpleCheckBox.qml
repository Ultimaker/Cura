// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// CheckBox widget for the on/off or true/false settings in the Machine Settings Dialog.
//
UM.TooltipArea
{
    UM.I18nCatalog { id: catalog; name: "cura"; }

    height: childrenRect.height
    width: childrenRect.width
    text: tooltip

    property alias containerStackId: propertyProvider.containerStackId
    property alias settingKey: propertyProvider.key
    property alias settingStoreIndex: propertyProvider.storeIndex

    property alias labelText: checkBox.text

    property string tooltip: propertyProvider.properties.description

    // callback functions
    property var forceUpdateOnChangeFunction: dummy_func

    // a dummy function for default property values
    function dummy_func() {}

    UM.SettingPropertyProvider
    {
        id: propertyProvider
        watchedProperties: [ "value", "description" ]
    }

    CheckBox
    {
        id: checkBox
        checked: String(propertyProvider.properties.value).toLowerCase() != 'false'
        onClicked:
        {
            propertyProvider.setPropertyValue("value", checked)
            forceUpdateOnChangeFunction()
        }
    }
}
