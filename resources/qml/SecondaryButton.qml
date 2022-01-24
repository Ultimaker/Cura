// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2

import UM 1.4 as UM
import Cura 1.1 as Cura


Cura.ActionButton
{
    color: UM.Theme.getColor("secondary_button")
    textColor: UM.Theme.getColor("secondary_button_text")
    outlineColor: UM.Theme.getColor("secondary_button_text")
    disabledColor: UM.Theme.getColor("action_button_disabled")
    textDisabledColor: UM.Theme.getColor("action_button_disabled_text")
    hoverColor: UM.Theme.getColor("secondary_button_hover")
}