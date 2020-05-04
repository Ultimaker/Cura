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

        source: UM.Theme.getIcon("checked")
        color: palette.text
    }

    Label
    {
        id: syncStateSuccessLabel
        text: catalog.i18nc("@info", "You are up to date")
        color: UM.Theme.getColor("text")
        font: UM.Theme.getFont("medium")
        renderType: Text.NativeRendering
    }
}