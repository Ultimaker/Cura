// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.0 as UM

Item
{
    id: wizardPage
    property string title

    SystemPalette{id: palette}

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
                text: wizardPage.title
                wrapMode: Text.WordWrap
                font.pointSize: 18
            }
            Label
            {
                id: pageDescription
                //: Add UM Original wizard page description
                width: parent.width
                wrapMode: Text.WordWrap
                text: qsTr("To assist you in having better default settings for your Ultimaker. Cura would like to know which upgrades you have in your machine:")
            }

            Column
            {
                id: pageCheckboxes
                width: parent.width

                CheckBox
                {
                    text: qsTr("Extruder driver ugrades")
                }
                CheckBox
                {
                    text: qsTr("Heated printer bed (kit)")
                }
                CheckBox
                {
                    text: qsTr("Heated printer bed (self built)")
                }
                CheckBox
                {
                    text: qsTr("Dual extrusion (experimental)")
                    checked: true
                }
            }

            Label
            {
                width: parent.width
                wrapMode: Text.WordWrap
                text: qsTr("If you have an Ultimaker bought after october 2012 you will have the Extruder drive upgrade. If you do not have this upgrade, it is highly recommended to improve reliability.");
            }

            Label
            {
                width: parent.width
                wrapMode: Text.WordWrap
                text: qsTr("This upgrade can be bought from the Ultimaker webshop or found on thingiverse as thing:26094");
            }
        }
    }

    ExclusiveGroup { id: printerGroup; }
}