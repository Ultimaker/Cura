import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

UM.PreferencesPage {
    //: General configuration page title
    title: qsTr("View");

    GridLayout {
        columns: 2;

        CheckBox {
            checked: UM.Preferences.getValue('view/show_overhang');
            onCheckedChanged: UM.Preferences.setValue('view/show_overhang', checked)

            text: qsTr("Display overhang");
        }

        Item { Layout.fillHeight: true; Layout.columnSpan: 2 }
    }
}
