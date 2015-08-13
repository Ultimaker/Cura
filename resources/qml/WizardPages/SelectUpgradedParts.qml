// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.0 as UM

ColumnLayout {
    id: wizardPage
    property string title
    property int pageWidth
    property int pageHeight

    SystemPalette{id: palette}
    //signal openFile(string fileName)
    //signal closeWizard()

    width: wizardPage.pageWidth
    height: wizardPage.pageHeight

    Connections {
        target: elementRoot
        onResize: {
            wizardPage.width = pageWidth
            wizardPage.height = pageHeight
        }
    }

    Label {
        text: parent.title
        font.pointSize: 18;
    }

    Label {
        //: Add UM Original wizard page description
        width: 300

        wrapMode: Text.WordWrap
        text: qsTr("To assist you in having better default settings for your Ultimaker. Cura would like to know which upgrades you have in your machine:");
    }

    ScrollView {
        Layout.fillWidth: true;
        Column {
            CheckBox {
                text: qsTr("Breakfast")
                checked: true
            }
            CheckBox {
                text: qsTr("Lunch")
            }
            CheckBox {
                text: qsTr("Dinner")
                checked: true
            }
        }
    }

    Label {
        //: Add Printer wizard field label
        text: qsTr("Printer Name:");
    }


    Item { Layout.fillWidth: true; Layout.fillHeight: true; }

    ExclusiveGroup { id: printerGroup; }
}