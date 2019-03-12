// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// TextArea widget for editing Gcode in the Machine Settings dialog.
//
UM.TooltipArea
{
    id: gcodeTextArea

    UM.I18nCatalog { id: catalog; name: "cura"; }

    height: childrenRect.height
    width: childrenRect.width
    text: tooltip

    property alias containerStackId: propertyProvider.containerStackId
    property alias settingKey: propertyProvider.key
    property alias settingStoreIndex: propertyProvider.storeIndex

    property string tooltip: propertyProvider.properties.description

    UM.SettingPropertyProvider
    {
        id: propertyProvider
        watchedProperties: [ "value", "description" ]
    }

    // TODO: put label here

    TextArea
    {
        id: gcodeArea
        width: areaWidth
        height: areaHeight
        font: UM.Theme.getFont("fixed")
        text: (propertyProvider.properties.value) ? propertyProvider.properties.value : ""
        wrapMode: TextEdit.NoWrap
        onActiveFocusChanged:
        {
            if (!activeFocus)
            {
                propertyProvider.setPropertyValue("value", text)
            }
        }
    }
}
