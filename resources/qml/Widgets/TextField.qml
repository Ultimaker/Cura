// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.7 as UM
import Cura 1.1 as Cura

UM.TextField
{
    id: control
    height: UM.Theme.getSize("setting_control").height
    leftPadding: UM.Theme.getSize("thin_margin").width
}
