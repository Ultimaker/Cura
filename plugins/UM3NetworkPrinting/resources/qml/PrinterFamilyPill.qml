import QtQuick 2.2
import QtQuick.Controls 1.4
import UM 1.2 as UM

Item
{
    property alias color: background.color
    property alias text: familyNameLabel.text
    property var padding: 0
    implicitHeight: familyNameLabel.contentHeight +  2 * padding // Apply the padding to top and bottom.
    implicitWidth: familyNameLabel.contentWidth + implicitHeight // The extra height is added to ensure the radius doesn't cut something off.
    Rectangle
    {
        id: background
        height: parent.height
        width: parent.width
        color: parent.color
        anchors.right: parent.right
        anchors.horizontalCenter: parent.horizontalCenter
        radius: 0.5 * height
    }
    Label
    {
        id: familyNameLabel
        anchors.centerIn: parent
        text: ""
    }
}