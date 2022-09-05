// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.9
import QtQuick.Layouts 2.10

import UM 1.5 as UM
import Cura 1.0 as Cura

UM.Dialog
{
    id: base

    backgroundColor: UM.Theme.getColor("background_2")

    property string machine_id_filter: ""
    ScrollView
    {
        anchors.fill: parent
        Column
        {
            anchors.fill: parent
            spacing: UM.Theme.getSize("default_margin").height

            Repeater
            {
                id: contents

                model: Cura.CompatibleMachineModel
                {
                    filter: machine_id_filter
                }

                delegate: Cura.PrintSelectorCard
                {
                    name: model.name
                    extruders: model.extruders
                }
            }
        }
    }
}
