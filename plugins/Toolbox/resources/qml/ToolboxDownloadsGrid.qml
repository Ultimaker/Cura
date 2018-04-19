// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.3
import UM 1.1 as UM

// TODO: Switch to QtQuick.Controls 2.x and remove QtQuick.Controls.Styles

Column
{
    id: base
    height: childrenRect.height
    spacing: UM.Theme.getSize("base_unit").height
    Label
    {
        id: heading
        text: toolbox.viewCategory == "material" ? catalog.i18nc("@label", "Maker Choices") : catalog.i18nc("@label", "Community Plugins")
        width: parent.width
        color: UM.Theme.getColor("text_medium")
        font: UM.Theme.getFont("medium")
    }
    GridLayout
    {
        id: grid
        width: parent.width
        columns: 2
        columnSpacing: UM.Theme.getSize("base_unit").width
        rowSpacing: UM.Theme.getSize("base_unit").height

        Repeater
        {
            model: toolbox.viewCategory == "material" ? toolbox.authorsModel : toolbox.packagesModel
            delegate: ToolboxDownloadsGridTile
            {
                Layout.preferredWidth: (grid.width - (grid.columns - 1) * grid.columnSpacing) / grid.columns
            }
        }
    }
}
