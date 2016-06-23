import UM 1.2 as UM
import Cura 1.0 as Cura

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

Cura.MachineAction
{
    anchors.fill: parent;
    Item
    {
        anchors.fill: parent;
        id: discoverUM3Action
        UM.I18nCatalog { id: catalog; name:"cura"}
        Label
        {
            id: pageTitle
            width: parent.width
            text: catalog.i18nc("@title", "Discover Printer")
            wrapMode: Text.WordWrap
            font.pointSize: 18;
        }
    }
}