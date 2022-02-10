import QtQuick 2.10
import QtQuick.Controls 2.2
import QtQuick.Window 2.1
import QtQuick.Layouts 1.1

import UM 1.5 as UM
import Cura 1.1 as Cura

UM.Dialog
{
    id: base

    minimumHeight: UM.Theme.getSize("small_popup_dialog").height
    minimumWidth: UM.Theme.getSize("small_popup_dialog").width / 1.5
    height: minimumHeight
    width: minimumWidth

    property alias color: colorInput.text

    margin: UM.Theme.getSize("default_margin").width
    buttonSpacing: UM.Theme.getSize("default_margin").width

    UM.Label
    {
        id: colorLabel
        font: UM.Theme.getFont("large")
        text: "Color Code (HEX)"
    }

    TextField
    {
        id: colorInput
        text: "#FFFFFF"
        anchors.top: colorLabel.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        validator: RegExpValidator { regExp: /^#([a-fA-F0-9]{6})$/ }
    }

    Rectangle
    {
        id: swatch
        color: base.color
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        anchors {
            left: colorInput.right
            top: colorInput.top
            bottom: colorInput.bottom
        }
        width: height
    }

    rightButtons:
    [
        Cura.PrimaryButton {
            text: catalog.i18nc("@action:button", "OK")
            onClicked: base.accept()
        },
        Cura.SecondaryButton {
            text: catalog.i18nc("@action:button", "Cancel")
            onClicked: base.close()
        }
    ]
}