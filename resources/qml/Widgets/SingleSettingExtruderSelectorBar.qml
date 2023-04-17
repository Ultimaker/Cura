// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.5 as Cura

// This component displays a row of extruder icons, clicking on the extruder will update the setting passed to "settingName"
// with the index of that extruder.
// This will only work for settings that take an extruder index.
Row
{
    id: extruderSelectionBar

    width: parent.width
    height: childrenRect.height
    spacing: 0

    property int selectedIndex: extruderSettingProvider.properties.value !== undefined ? extruderSettingProvider.properties.value : 0
    property alias model: extruderButtonRepeater.model
    property alias extruderSettingName: extruderSettingProvider.key
    property alias containerStack: extruderSettingProvider.containerStack

    property UM.SettingPropertyProvider extruderSettingProvider: UM.SettingPropertyProvider
    {
        id: extruderSettingProvider
        containerStack: Cura.MachineManager.activeMachine
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    function onClickExtruder(index)
    {
        forceActiveFocus();
        extruderSettingProvider.setPropertyValue("value", index);
    }


    Repeater
    {
        id: extruderButtonRepeater

        model: CuraApplication.getExtrudersModel()

        delegate: Item
        {
            width: {
                // This will "squish" the extruder buttons together when the fill up the horizontal space
                const maximum_width = Math.floor(extruderSelectionBar.width / extruderButtonRepeater.count);
                return Math.min(UM.Theme.getSize("large_button").width, maximum_width);
            }
            height: childrenRect.height

            Cura.ExtruderButton
            {
                anchors.margins: 0
                padding: 0
                extruder: model
                checked: extruder.index === selectedIndex
                iconScale: 0.8
                font: UM.Theme.getFont("tiny_emphasis")
                buttonSize: UM.Theme.getSize("small_button").width
                onClicked: extruder.enabled && onClickExtruder(extruder.index)
            }
        }
    }
}
