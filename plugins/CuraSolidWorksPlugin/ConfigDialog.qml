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
    width: 300 * Screen.devicePixelRatio
    minimumWidth: 300 * Screen.devicePixelRatio

    height: 100 * Screen.devicePixelRatio
    minimumHeight: 100 * Screen.devicePixelRatio

    title: catalog.i18nc("@title:window", "Cura SolidWorks Plugin Configuration")

    onVisibilityChanged:
    {
        if (visible)
        {
            choiceDropdown.updateCurrentIndex();
        }
    }

    GridLayout
    {
        UM.I18nCatalog{id: catalog; name: "cura"}
        anchors.fill: parent
        Layout.fillWidth: true
        columnSpacing: 16
        rowSpacing: 10
        columns: 1

        Row
        {
            width: parent.width

            Label {
                text: catalog.i18nc("@action:label", "Default quality of the exported STL:")
                width: 150
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        Row
        {
            ComboBox
            {
                id: choiceDropdown

                currentIndex: updateCurrentIndex()

                function updateCurrentIndex()
                {
                    var index = 0;
                    var currentChoice = UM.Preferences.getValue("cura_solidworks/choice_on_exporting_stl_quality");
                    for (var i = 0; i < model.count; ++i)
                    {
                        if (model.get(i).code == currentChoice)
                        {
                            index = i;
                            break;
                        }
                    }
                    currentIndex = index;
                }

                model: ListModel
                {
                    id: choiceModel

                    Component.onCompleted:
                    {
                        append({ text: catalog.i18nc("@option:curaSolidworksStlQuality", "Always ask"), code: "always_ask" });
                        append({ text: catalog.i18nc("@option:curaSolidworksStlQuality", "Always use Fine quality"), code: "always_use_fine" });
                        append({ text: catalog.i18nc("@option:curaSolidworksStlQuality", "Always use Coarse quality"), code: "always_use_coarse" });
                    }
                }
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
                UM.Preferences.setValue("cura_solidworks/choice_on_exporting_stl_quality",
                    choiceModel.get(choiceDropdown.currentIndex).code);
                close();
            }
            enabled: true
        },
        Button
        {
            id: cancel_button
            text: catalog.i18nc("@action:button", "Cancel")
            onClicked:
            {
                close();
            }
            enabled: true
        }
    ]
}
