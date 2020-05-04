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

        RotationAnimator
        {
            id: updateAnimator
            target: updateImage
            from: 0
            to: 360
            duration: 1000
            loops: Animation.Infinite
            running: true
        }
    }

    Label
    {
        id: accountSyncButton
        text: catalog.i18nc("@button", "Checking...")
        color: UM.Theme.getColor("text")
        font: UM.Theme.getFont("medium")
        renderType: Text.NativeRendering
    }
}