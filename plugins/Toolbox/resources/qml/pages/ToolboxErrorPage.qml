// Copyright (c) 2021 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.1
import UM 1.5 as UM

UM.Label
{
    text: catalog.i18nc("@info", "Could not connect to the Cura Package database. Please check your connection.")
    anchors.centerIn: parent
}
