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
    property var isCheckedFunction // Function that accepts the modelItem and returns if the item should be active.

    implicitWidth: 200
    implicitHeight: checkboxSize

    property var dataModel: null

    // The horizontal inactive bar that sits behind the buttons
    Rectangle
    {
        id: inactiveLine
        color: inactiveColor

        height: barSize

        // This can (and should) be done wiht a verticalCenter. For some reason it does work in QtCreator
        // but not when using the exact same QML in Cura.
        y: 0.5 * checkboxSize
        anchors
        {
            left: buttonBar.left
            right: buttonBar.right
            leftMargin: (checkboxSize - inactiveMarkerSize) / 2
            rightMargin: (checkboxSize - inactiveMarkerSize) / 2
        }
    }


    RowLayout
    {
        id: buttonBar
        anchors.top: parent.top
        height: checkboxSize
        width: parent.width
        spacing: 0

        Repeater
        {
            id: repeater
            model: base.dataModel
            height: checkboxSize
            Item
            {
                Layout.fillWidth: true
                // The last item of the repeater needs to be shorter, as we don't need another part to fit
                // the horizontal bar. The others should essentially not be limited.
                Layout.maximumWidth: index + 1 === repeater.count ? activeComponent.width: 200000000
                height: activeComponent.height
                property bool isEnabled: model.available
                // The horizontal bar between the checkable options.
                // Note that the horizontal bar points towards the previous item.
                Rectangle
                {
                    property Item previousItem: repeater.itemAt(index - 1)

                    height: barSize
                    width: buttonBar.width / (repeater.count - 1) - activeComponent.width - 2
                    color: defaultItemColor
                    // This can (and should) be done wiht a verticalCenter. For some reason it does work in QtCreator
                    // but not when using the exact same QML in Cura.
                    y: 0.5 * checkboxSize
                    anchors
                    {
                        right: activeComponent.left
                    }
                    visible: previousItem !== null && previousItem.isEnabled && isEnabled
                }
                Loader
                {
                    id: activeComponent
                    sourceComponent: isEnabled? checkboxComponent : disabledComponent
                    width: checkboxSize

                    property var modelItem: model
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
            width: checkboxSize

            Rectangle
            {
                // This can (and should) be done wiht a verticalCenter. For some reason it does work in QtCreator
                // but not when using the exact same QML in Cura.
                y: 0.5 * checkboxSize - 1
                anchors.horizontalCenter: parent.horizontalCenter
                height: inactiveMarkerSize
                width: inactiveMarkerSize
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
            property var modelData: modelItem

            checked: isCheckedFunction(modelItem)
            indicator: Rectangle
            {
                height: checkboxSize
                width: checkboxSize
                radius: width / 2

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
