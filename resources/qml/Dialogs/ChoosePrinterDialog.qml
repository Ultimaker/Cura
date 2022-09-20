// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.9
import QtQuick.Layouts 2.10

import UM 1.5 as UM
import Cura 1.0 as Cura

UM.Dialog
{
    property var manager
    property var compatible_machine_model: Cura.CompatibleMachineModel {}
    id: base

    title: catalog.i18nc("@title:window", "Select Printer")

    backgroundColor: UM.Theme.getColor("background_2")

    width: minimumWidth
    minimumWidth: 550 * screenScaleFactor
    height: minimumHeight
    minimumHeight: 550 * screenScaleFactor

    modality: Qt.ApplicationModal

    ScrollView
    {
        // Workaround for Windowing bugs in Qt:
        width: 550 * screenScaleFactor - 3 * UM.Theme.getSize("default_margin").width
        height: 550 * screenScaleFactor - 3 * UM.Theme.getSize("default_margin").height

        UM.I18nCatalog
        {
            id: catalog
            name: "cura"
        }

        anchors.fill: parent
        Column
        {
            anchors.fill: parent
            spacing: UM.Theme.getSize("default_margin").height

            Item
            {
                width: parent.width
                height: childrenRect.height

                UM.Label
                {
                    anchors.left: parent.left
                    text: catalog.i18nc("@title:label", "Compatible Printers")
                    font: UM.Theme.getFont("large")
                }

                UM.SimpleButton
                {
                    anchors.right: parent.right

                    width: UM.Theme.getSize("small_button").width
                    height: UM.Theme.getSize("small_button").height
                    iconSource: UM.Theme.getIcon("ArrowDoubleCircleRight")
                    color: UM.Theme.getColor("text_link")
                    hoverColor: UM.Theme.getColor("text_scene_hover")

                    onClicked:
                    {
                        manager.refresh()
                        base.compatible_machine_model.forceUpdate()
                    }
                }
            }

            Repeater
            {
                id: contents

                model: base.compatible_machine_model

                delegate: Cura.PrintSelectorCard
                {
                    name: model.name
                    unique_id: model.unique_id
                    extruders: model.extruders
                    manager: base.manager
                }
            }

            UM.Label
            {
                visible: contents.count < 1
                text: catalog.i18nc("@description", "No compatible printers, that are currently online, where found.")
            }
        }
    }
}
