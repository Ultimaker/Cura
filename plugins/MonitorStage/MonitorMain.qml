import QtQuick 2.10
import QtQuick.Controls 2.0
import UM 1.5 as UM

Rectangle
{
    id: viewportOverlay
    color: UM.Theme.getColor("viewport_overlay")
    anchors.fill: parent

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    Text
    {
        anchors.centerIn: parent
        text: "Hello World"
        font.pointSize: 24
        color: "white"
    }
}