import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3


Item
{
    id: base
    anchors.fill: parent

    TabBar
    {
        id: bar
        width: parent.width
        TabButton
        {
            text: "Printer"
        }

        Repeater
        {
            id: extrudersTabsRepeater
            model: ["Extruder 1", "Extruder 2", "Extruder 3"]

            TabButton
            {
                text: modelData
            }
        }
    }

    StackLayout
    {
        width: parent.width
        currentIndex: bar.currentIndex
        Item
        {
            id: printerTab
        }
        Repeater
        {
            model: ["Extruder 1", "Extruder 2", "Extruder 3"]
            Item
            {
                anchors.centerIn: parent

                Label  // TODO: this is a dummy
                {
                    anchors.centerIn: parent
                    text: modelData
                }
            }
        }
    }
}
