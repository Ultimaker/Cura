// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.0 as UM

UM.PreferencesPage {
    id: preferencesPage

    //: View configuration page title
    title: qsTr("View");

    function reset()
    {
        UM.Preferences.resetPreference("view/show_overhang");
    }

    GridLayout {
        columns: 2;

        CheckBox {
            id: viewCheckbox
            checked: UM.Preferences.getValue("view/show_overhang")
            onCheckedChanged: UM.Preferences.setValue("view/show_overhang", checked)
        }
        Button {
            id: viewText //is a button so the user doesn't have te click inconvenientley precise to enable or disable the checkbox

            //: Display Overhang preference checkbox
            text: qsTr("Display Overhang");
            onClicked: viewCheckbox.checked = !viewCheckbox.checked

            //: Display Overhang preference tooltip
            tooltip: "Highlight unsupported areas of the model in red. Without support these areas will nog print properly."

            style: ButtonStyle {
                background: Rectangle {
                    border.width: 0
                    color: "transparent"
                }
                label: Text {
                    renderType: Text.NativeRendering
                    horizontalAlignment: Text.AlignLeft
                    text: control.text
                }
            }
        }
        Item { Layout.fillHeight: true; Layout.columnSpan: 2 }
    }
}
