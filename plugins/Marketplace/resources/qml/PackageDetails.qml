// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.3

import Cura 1.0 as Cura
import UM 1.0 as UM

Item
{
    Column
    {
        anchors.fill: parent
        anchors.margins: UM.Theme.getSize("default_margin").width

        RowLayout
        {
            spacing: UM.Theme.getSize("default_margin").width

            Cura.SecondaryButton
            {
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredHeight: UM.Theme.getSize("action_button").height
                Layout.preferredWidth: height

                onClicked: contextStack.pop() //Remove this page, returning to the main package list or whichever thing is beneath it.

                tooltip: catalog.i18nc("@button:tooltip", "Back")
                toolTipContentAlignment: Cura.ToolTip.ContentAlignment.AlignRight
                leftPadding: UM.Theme.getSize("narrow_margin").width
                rightPadding: leftPadding
                iconSource: UM.Theme.getIcon("ArrowLeft")
                iconSize: height - leftPadding * 2
            }

            Label
            {
                Layout.alignment: Qt.AlignVCenter

                text: "Install Plug-ins" //TODO: Depend on package type, and translate.
                font: UM.Theme.getFont("large")
                color: UM.Theme.getColor("text")
            }
        }
    }
}