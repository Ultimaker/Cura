//Copyright (c) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15

import Cura 1.6 as Cura
import UM 1.6 as UM

//Message showing the user that the configuration they have selected has no profiles.
Column
{
    spacing: UM.Theme.getSize("default_margin").height

    Row
    {
        width: parent.width

        spacing: UM.Theme.getSize("thin_margin").width

        UM.StatusIcon
        {
            width: UM.Theme.getSize("notification_icon").width
            status: UM.StatusIcon.Status.ERROR
        }

        UM.Label
        {
            width: parent.width

            font: UM.Theme.getFont("default_bold")
            text: catalog.i18nc("@error", "Configuration not supported")
        }
    }

    UM.Label
    {
        width: parent.width

        text: catalog.i18nc("@message:text %1 is the name the printer uses for 'nozzle'.", "No profiles are available for the selected material/%1 configuration. Please change your configuration."
            ).arg(Cura.MachineManager.activeDefinitionVariantsName)
    }

    Cura.TertiaryButton
    {
        anchors.right: parent.right

        text: catalog.i18nc("@button:label", "Learn more")
        textFont: UM.Theme.getFont("default")
        iconSource: UM.Theme.getIcon("LinkExternal")
        isIconOnRightSide: true

        onClicked: Qt.openUrlExternally("https://support.ultimaker.com/hc/en-us/articles/360012909099")
    }
}