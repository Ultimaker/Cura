import QtQuick 2.0
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
Item
{
    id: base
    property ButtonGroup buttonGroup: null

    property color activeColor: "#3282ff"
    property color inactiveColor: "#cccccc"
    property color defaultItemColor: "#0a0850"
    property int checkboxSize: 14
    property int inactiveMarkerSize: 4
    property int barSize: 2

    implicitWidth: 200
    implicitHeight: buttonBar.height

    property var model: null

    // The horizontal inactive bar that sits behind the buttons
    Rectangle
    {
        id: inactiveLine
        color: inactiveColor
        anchors.verticalCenter: buttonBar.verticalCenter
        height: barSize
        width: buttonBar.width
    }

    RowLayout
    {
        id: buttonBar
        height: childrenRect.height
        width: parent.width
        spacing: 0
        Repeater
        {
            id: repeater
            model: base.model

            Item
            {
                Layout.fillWidth: true
                // The last item of the repeater needs to be shorter, as we don't need another part to fit
                // the horizontal bar. The others should essentially not be limited.
                Layout.maximumWidth: index + 1 === repeater.count ? activeComponent.width: 200000000
                height: activeComponent.height

                property bool isEnabled: model.enabled
                // The horizontal bar between the checkable options.
                // Note that the horizontal bar points towards the previous item.
                Rectangle
                {
                    property Item previousItem: repeater.itemAt(index - 1)

                    height: barSize
                    width: parent.width - activeComponent.width
                    color: defaultItemColor

                    anchors
                    {
                        right: activeComponent.left
                        verticalCenter: activeComponent.verticalCenter
                    }
                    visible:  previousItem !== null && previousItem.isEnabled && isEnabled
                }
                Loader
                {
                    id: activeComponent
                    sourceComponent: isEnabled? checkboxComponent : disabledComponent
                }
            }
        }
    }

    Component
    {
        id: disabledComponent
        Item
        {
            height: checkboxSize
            width: inactiveMarkerSize
            Rectangle
            {
                anchors.centerIn: parent
                height: parent.width
                width: parent.width
                radius: width / 2
                color: inactiveColor
            }
        }
    }

    Component
    {
        id: checkboxComponent
        CheckBox
        {
            id: checkbox
            ButtonGroup.group: buttonGroup
            width: checkboxSize
            height: checkboxSize
            indicator: Rectangle
            {
                height: checkbox.height
                width: checkbox.width
                radius: width / 2

                anchors.centerIn: checkbox
                border.color: defaultItemColor

                Rectangle
                {
                    anchors
                    {
                        margins: 3
                        fill: parent
                    }
                    radius: width / 2
                    color: activeColor
                    visible: checkbox.checked
                }
            }
        }
    }
}
