// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM

Item
{
    id: wizardPage
    property string title

    SystemPalette{id: palette}
    UM.I18nCatalog { id: catalog; name:"cura"}
    ScrollView
    {
        height: parent.height
        width: parent.width
        Column
        {
            width: wizardPage.width
            Label
            {
                id: pageTitle
                width: parent.width
                text: catalog.i18nc("@title", "Upgrade Firmware")
                wrapMode: Text.WordWrap
                font.pointSize: 18
            }
            Label
            {
                id: pageDescription
                width: parent.width
                wrapMode: Text.WordWrap
                text: catalog.i18nc("@label","Firmware is the piece of software running directly on your 3D printer. This firmware controls the step motors, regulates the temperature and ultimately makes your printer work.")
            }

            Label
            {
                width: parent.width
                wrapMode: Text.WordWrap
                text: catalog.i18nc("@label","The firmware shipping with new Ultimakers works, but upgrades have been made to make better prints, and make calibration easier.");
            }

            Label
            {
                width: parent.width
                wrapMode: Text.WordWrap
                text: catalog.i18nc("@label","Cura requires these new features and thus your firmware will most likely need to be upgraded. You can do so now.");
            }
            Button {
                text: catalog.i18nc("@action:button","Upgrade to Marlin Firmware");
            }
            Button {
                text: catalog.i18nc("@action:button","Skip Upgrade");
            }
        }
    }

    ExclusiveGroup { id: printerGroup; }
}