import UM 1.1 as UM
import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.1

UM.Dialog
{
    id: base

    title: "YAY"
    width: 450
    height: 150
    ListView
    {
        model: manager.pluginsModel
        anchors.fill: parent
        delegate: Row
        {
            width: parent.width
            Button
            {
                text: model.name
            }
            Button
            {
                text: model.author
            }

            Label
            {
                text: model.short_description
            }
        }
    }
}