// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

// TODO: Switch to QtQuick.Controls 2.x and remove QtQuick.Controls.Styles

Column
{
    id: base
    height: childrenRect.height
    spacing: UM.Theme.getSize("toolbox_showcase_spacing").width
    Label
    {
        id: heading
        text: catalog.i18nc("@label", "Featured")
        width: parent.width
        color: UM.Theme.getColor("text_medium")
        font: UM.Theme.getFont("medium")
    }
    Row
    {
        height: childrenRect.height
        spacing: UM.Theme.getSize("base_unit").width * 2
        anchors
        {
            horizontalCenter: parent.horizontalCenter
        }

        Repeater
        {
            model: {
                if ( toolbox.viewCategory == "plugin" )
                {
                    return toolbox.pluginsShowcaseModel
                }
                if ( toolbox.viewCategory == "material" )
                {
                    return toolbox.materialsShowcaseModel
                }
            }
            delegate: ToolboxDownloadsShowcaseTile {}
        }
    }
}
