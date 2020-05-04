import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.4 as UM
import Cura 1.1 as Cura

Row // sync state icon + message
{
    width: childrenRect.width
    height: childrenRect.height
    anchors.horizontalCenter: parent.horizontalCenter
    spacing: UM.Theme.getSize("narrow_margin").height



    UM.RecolorImage
    {
        id: updateImage
        width: 20 * screenScaleFactor
        height: width

        source: UM.Theme.getIcon("update")
        color: palette.text

    }

    Label
    {
        id: accountSyncButton
        text: catalog.i18nc("@button", "Check for account updates")
        color: UM.Theme.getColor("secondary_button_text")
        font: UM.Theme.getFont("medium")
        renderType: Text.NativeRendering

        MouseArea
        {
            anchors.fill: parent
            onClicked: Cura.API.account.sync()
            hoverEnabled: true
            onEntered: accountSyncButton.font.underline = true
            onExited: accountSyncButton.font.underline = false
        }
    }
}