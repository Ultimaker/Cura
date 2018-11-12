import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.2 as UM

// The expandable component has 3 major sub components:
//      * The headerItem; Always visible and should hold some info about what happens if the component is expanded
//      * The popupItem; The content that needs to be shown if the component is expanded.
//      * The Icon; An icon that is displayed on the right of the drawer.
Item
{
    // The headerItem holds the QML item that is always displayed.
    property alias headerItem: headerItemLoader.sourceComponent

    // The popupItem holds the QML item that is shown when the "open" button is pressed
    property var popupItem

    // The background color of the popup
    property color popupBackgroundColor: "white"

    property alias headerBackgroundColor: background.color

    // How much spacing is needed around the popupItem
    property alias popupPadding: popup.padding

    // How much padding is needed around the header & button
    property alias headerPadding: background.padding

    // What icon should be displayed on the right.
    property alias iconSource: collapseButton.source

    // What is the color of the icon?
    property alias iconColor: collapseButton.color

    // The icon size (it's always drawn as a square)
    property alias iconSize: collapseButton.width

    // Is the "drawer" open?
    readonly property alias expanded: popup.visible

    onPopupItemChanged:
    {
        // Since we want the size of the popup to be set by the size of the content,
        // we need to do it like this.
        popup.width = popupItem.width + 2 * popup.padding
        popup.height = popupItem.height + 2 * popup.padding
        popup.contentItem = popupItem
    }

    implicitHeight: 100
    implicitWidth: 400
    Rectangle
    {
        id: background
        property real padding: UM.Theme.getSize("default_margin").width

        color: "white"
        anchors.fill: parent
        Loader
        {
            id: headerItemLoader
            anchors
            {
                left: parent.left
                right: collapseButton.left
                top: parent.top
                bottom: parent.bottom
                margins: background.padding
            }
        }

        UM.RecolorImage
        {
            id: collapseButton
            anchors
            {
                right: parent.right
                verticalCenter: parent.verticalCenter
                margins: background.padding
            }
            sourceSize.width: width
            sourceSize.height: height
            visible: source != ""
            width: UM.Theme.getSize("section_icon").width
            height: width
            color: "black"
        }

        MouseArea
        {
            anchors.fill: parent
            onClicked: popup.visible ? popup.close() : popup.open()
        }
    }

    Popup
    {
        id: popup

        // Ensure that the popup is located directly below the headerItem
        y: headerItemLoader.height + 2 * background.padding

        // Make the popup right aligned with the rest. The 3x padding is due to left, right and padding between
        //the button & text.
        x: -width + collapseButton.width + headerItemLoader.width + 3 * background.padding

        closePolicy: Popup.CloseOnPressOutsideParent

        background: Rectangle
        {
            color: popupBackgroundColor
        }
    }
}
