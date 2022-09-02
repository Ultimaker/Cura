// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.9

import UM 1.5 as UM
import Cura 1.0 as Cura

UM.Dialog
{
    id: base

    property string machine_id_filter: ""

    Column
    {
        anchors.fill: parent

        Repeater
        {
            id: contents

            model: Cura.CompatibleMachineModel
            {
                filter: machine_id_filter
            }
            delegate: UM.Label
            {
                text: model.name
            }
        }
    }
}
