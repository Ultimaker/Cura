// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

UM.PreferencesPage {
    //: View configuration page title
    title: qsTr("View");

    function reset()
    {
        UM.Preferences.resetPreference("view/show_overhang");
    }

    GridLayout {
        columns: 2;

        CheckBox {
            checked: UM.Preferences.getValue("view/show_overhang");
            onCheckedChanged: UM.Preferences.setValue("view/show_overhang", checked)

            //: Display Overhang preference checkbox
            text: qsTr("Display Overhang");
        }

        Item { Layout.fillHeight: true; Layout.columnSpan: 2 }
    }
}
