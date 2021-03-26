import UM 1.1 as UM //This allows you to use all of Uranium's built-in QML items.
import QtQuick 2.2 //This allows you to use QtQuick's built-in QML items.
import QtQuick.Controls 1.1 //Contains the "Label" element.

UM.Dialog //Creates a modal window that pops up above the interface.
{
    id: base

    width: 200
    height: 200
    minimumWidth: 200
    minimumHeight: 200

    Label
    {
        id: id_label

        //Positions the label on the top-left side of the window.
        anchors.top: base.top
        anchors.topMargin: 10
        anchors.left: base.left
        anchors.leftMargin: 10

        text: "Selected objects: "
    }
    Text
    {
        //Positions this text right of the accompanying label.
        anchors.verticalCenter: id_label.verticalCenter
        anchors.left: id_label.right

        text: UM.Selection.selectionNames.join()
    }
}