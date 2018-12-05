// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Controls 2.0
import UM 1.3 as UM

Rectangle {
    color: UM.Theme.getColor("monitor_lining_light"); // TODO: Maybe theme separately? Maybe not.
    height: UM.Theme.getSize("default_lining").height;
    width: parent.width;
}