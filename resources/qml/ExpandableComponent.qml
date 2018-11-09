import QtQuick 2.7
import QtQuick.Controls 2.3

// The expandable component has 3 major sub components:
//      * The headerItem; Always visible and should hold some info about what happens if the component is expanded
//      * The popupItem; The content that needs to be shown if the component is expanded.
//      * The Button; The actual button that expands the popup.
Item
{
    // The headerItem holds the QML item that is always displayed.
    property alias headerItem: headerItemLoader.sourceComponent

    // The popupItem holds the QML item that is shown when the "open" button is pressed
    property var popupItem

    // The background color of the popup
    property color popupBackgroundColor: "white"

    // How much spacing is needed around the popupItem
    property alias padding: popup.padding

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

    Loader
    {
        id: headerItemLoader
        anchors
        {
            left: parent.left
            right: collapseButton.left
            top: parent.top
            bottom: parent.bottom
        }
    }

    Button
    {
        id: collapseButton
        anchors
        {
            right: parent.right
            top: parent.top
            bottom: parent.bottom
        }
        text: popup.visible ? "close" : "open"
        onClicked: popup.visible ? popup.close() : popup.open()
    }

    Popup
    {
        id: popup

        // Ensure that the popup is located directly below the headerItem
        y: headerItemLoader.height

        // Make the popup right aligned with the rest.
        x: -width + collapseButton.width + headerItemLoader.width

        closePolicy: Popup.CloseOnPressOutsideParent

        background: Rectangle
        {
            id: background
            color: popupBackgroundColor
        }
    }
}
