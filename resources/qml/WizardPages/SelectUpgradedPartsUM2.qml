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

    property variant wizard: null;

    Connections
    {
        target: wizardPage.wizard
        onNextClicked: //You can add functions here that get triggered when the final button is clicked in the wizard-element
        {
            if(wizardPage.wizard.lastPage ==  true){
                wizardPage.wizard.visible = false
            }
        }
    }

    Component.onDestruction:
    {
        if (hotendCheckBox.checked == true){
            switch(UM.MachineManager.getMachineDefinitionType()) {
                case "ultimaker2":
                    UM.MachineManager.setMachineDefinitionType("ultimaker2_olsson")
                    break;
                case "ultimaker2_extended":
                    UM.MachineManager.setMachineDefinitionType("ultimaker2_extended_olsson")
                    break;
            }
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
            id: hotendCheckBox
            text: catalog.i18nc("@option:check","Olsson Block")
            checked: false
        }
    }

    ExclusiveGroup { id: printerGroup; }
}
