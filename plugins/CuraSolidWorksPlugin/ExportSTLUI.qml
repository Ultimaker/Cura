// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.2 as UM
import Cura 1.0 as Cura

UM.Dialog
{
    width: 300 * Screen.devicePixelRatio;
    minimumWidth: 300 * Screen.devicePixelRatio;

    height: 100 * Screen.devicePixelRatio;
    minimumHeight: 100 * Screen.devicePixelRatio;

    title: catalog.i18nc("@title:window", "Import SolidWorks File as STL...")

    onVisibilityChanged:
    {
        if (visible)
        {
            qualityDropdown.currentIndex = 1;
            rememberChoiceCheckBox.checked = UM.Preferences.getValue("cura_solidworks/choice_on_exporting_stl_quality") != "always_ask";
        }
    }

    GridLayout
    {
        UM.I18nCatalog{id: catalog; name: "cura"}
        anchors.fill: parent;
        Layout.fillWidth: true
        columnSpacing: 16
        rowSpacing: 4
        columns: 1

        UM.TooltipArea {
            Layout.fillWidth:true
            height: childrenRect.height
            text: catalog.i18nc("@info:tooltip", "Quality of the Exported STL")
            Row {
                width: parent.width

                Label {
                    text: catalog.i18nc("@action:label", "Quality")
                    width: 100
                    anchors.verticalCenter: parent.verticalCenter
                }

                ComboBox
                {
                    id: qualityDropdown
                    model: ListModel
                    {
                        id: qualityModel

                        Component.onCompleted:
                        {
                            append({ text: catalog.i18nc("@option:curaSolidworksStlQuality", "Coarse"), code: "coarse" });
                            append({ text: catalog.i18nc("@option:curaSolidworksStlQuality", "Fine"), code: "fine" });
                        }
                    }
                    currentIndex: 1
                }
            }
        }

        Row
        {
            width: parent.width

            CheckBox
            {
                id: rememberChoiceCheckBox
                text: catalog.i18nc("@text:window", "Remember my choice")
                checked: UM.Preferences.getValue("cura_solidworks/choice_on_exporting_stl_quality") != "always_ask"
            }
        }
    }

    rightButtons: [
        Button
        {
            id: ok_button
            text: catalog.i18nc("@action:button", "OK")
            onClicked:
            {
                manager.setQuality(qualityModel.get(qualityDropdown.currentIndex).code, rememberChoiceCheckBox.checked);
                manager.onOkButtonClicked();
            }
            enabled: true
        },
        Button
        {
            id: cancel_button
            text: catalog.i18nc("@action:button", "Cancel")
            onClicked:
            {
                manager.onCancelButtonClicked();
            }
            enabled: true
        }
    ]
}
