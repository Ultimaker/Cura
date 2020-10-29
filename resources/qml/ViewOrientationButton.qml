// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2

import UM 1.4 as UM

UM.SimpleButton
{
    width: UM.Theme.getSize("small_button").width
    height: UM.Theme.getSize("small_button").height
    hoverColor: UM.Theme.getColor("small_button_text_hover")
    color: UM.Theme.getColor("small_button_text")
    iconMargin: UM.Theme.getSize("thick_lining").width
}