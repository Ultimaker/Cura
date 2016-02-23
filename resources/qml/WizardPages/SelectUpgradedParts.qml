// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM

Item
{
    id: wizardPage
    property string title

    SystemPalette{id: palette}
    UM.I18nCatalog { id: catalog; name:"cura"}

    Component.onDestruction:
    {
        if (extruderCheckBox.checked == true){
            UM.MachineManager.setMachineSettingValue("machine_extruder_drive_upgrade", true)
        }
        if (heatedBedCheckBox1.checked == true || heatedBedCheckBox2.checked == true){
            UM.MachineManager.setMachineSettingValue("machine_heated_bed", true)
        }
    }
    Label
    {
        id: pageTitle
        width: parent.width
        text: catalog.i18nc("@title", "Select Upgraded Parts")
        wrapMode: Text.WordWrap
        font.pointSize: 18
    }
    Label
    {
        id: pageDescription
        anchors.top: pageTitle.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: parent.width
        wrapMode: Text.WordWrap
        text: catalog.i18nc("@label","To assist you in having better default settings for your Ultimaker. Cura would like to know which upgrades you have in your machine:")
    }

    Item
    {
        id: pageCheckboxes
        height: childrenRect.height
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        anchors.top: pageDescription.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: parent.width - UM.Theme.getSize("default_margin").width
        CheckBox
        {
            id: extruderCheckBox
            text: catalog.i18nc("@option:check","Extruder driver ugrades")
            checked: true
        }
        CheckBox
        {
            id: heatedBedCheckBox1
            text: catalog.i18nc("@option:check","Heated printer bed")
            y: extruderCheckBox.height * 1
            checked: false
            onClicked: {
                if (heatedBedCheckBox2.checked == true)
                    heatedBedCheckBox2.checked = false
            }
        }
        CheckBox
        {
            id: heatedBedCheckBox2
            text: catalog.i18nc("@option:check","Heated printer bed (self built)")
            y: extruderCheckBox.height * 2
            checked: false
            onClicked: {
                if (heatedBedCheckBox1.checked == true)
                    heatedBedCheckBox1.checked = false
            }
        }
    }

    Label
    {
        width: parent.width
        anchors.top: pageCheckboxes.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        wrapMode: Text.WordWrap
        text: catalog.i18nc("@label","If you bought your Ultimaker after october 2012 you will have the Extruder drive upgrade. If you do not have this upgrade, it is highly recommended to improve reliability. This upgrade can be bought from the Ultimaker webshop or found on thingiverse as thing:26094");
    }

    ExclusiveGroup { id: printerGroup; }
}
