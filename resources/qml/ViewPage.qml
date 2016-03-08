// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.1 as UM

UM.PreferencesPage
{
    id: preferencesPage

    //: View configuration page title
    title: catalog.i18nc("@title:window","View");

    function reset()
    {
        UM.Preferences.resetPreference("view/show_overhang");
        UM.Preferences.resetPreference("view/center_on_select");
    }

    Column
    {
        UM.I18nCatalog { id: catalog; name:"cura"}

        UM.TooltipArea
        {
            width: childrenRect.width;
            height: childrenRect.height;

            text: catalog.i18nc("@info:tooltip","Highlight unsupported areas of the model in red. Without support these areas will not print properly.")

            CheckBox
            {
                id: overhangCheckbox

                checked: boolCheck(UM.Preferences.getValue("view/show_overhang"))
                onClicked: UM.Preferences.setValue("view/show_overhang",  checked)

                text: catalog.i18nc("@option:check","Display overhang");
            }
        }

        UM.TooltipArea {
            width: childrenRect.width;
            height: childrenRect.height;
            text: catalog.i18nc("@info:tooltip","Moves the camera so the object is in the center of the view when an object is selected")

            CheckBox
            {
                id: centerCheckbox
                text: catalog.i18nc("@action:button","Center camera when item is selected");
                checked: boolCheck(UM.Preferences.getValue("view/center_on_select"))
                onClicked: UM.Preferences.setValue("view/center_on_select",  checked)
            }
        }

        Connections {
            target: UM.Preferences
            onPreferenceChanged:
            {
                overhangCheckbox.checked = boolCheck(UM.Preferences.getValue("view/show_overhang"))
                centerCheckbox.checked = boolCheck(UM.Preferences.getValue("view/center_on_select"))
            }
        }
    }
}
