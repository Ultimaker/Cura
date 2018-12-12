// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.2 as UM


Button
{
    id: modelCheckerButton

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    visible: manager.hasWarnings
    tooltip: catalog.i18nc("@info:tooltip", "Some things could be problematic in this print. Click to see tips for adjustment.")
    onClicked: manager.showWarnings()

    width: UM.Theme.getSize("save_button_specs_icons").width
    height: UM.Theme.getSize("save_button_specs_icons").height

    anchors.verticalCenter: parent ? parent.verticalCenter : undefined

    style: ButtonStyle
    {
        background: Item
        {
            UM.RecolorImage
            {
                width: UM.Theme.getSize("save_button_specs_icons").width;
                height: UM.Theme.getSize("save_button_specs_icons").height;
                sourceSize.height: width;
                color: control.hovered ? UM.Theme.getColor("text_scene_hover") : UM.Theme.getColor("text_scene");
                source: "model_checker.svg"
            }
        }
    }
}
