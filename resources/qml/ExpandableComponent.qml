import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.2 as UM

// The expandable component has 3 major sub components:
//      * The headerItem; Always visible and should hold some info about what happens if the component is expanded
//      * The popupItem; The content that needs to be shown if the component is expanded.
//      * The icon; An icon that is displayed on the right of the drawer.
Item
{
    id: base
    // The headerItem holds the QML item that is always displayed.
    property alias headerItem: headerItemLoader.sourceComponent

    // The popupItem holds the QML item that is shown when the "open" button is pressed
    property var popupItem

    property color popupBackgroundColor: UM.Theme.getColor("action_button")
    property int popupBorderWidth: UM.Theme.getSize("default_lining").width
    property color popupBorderColor: UM.Theme.getColor("lining")

    property color headerBackgroundColor: UM.Theme.getColor("action_button")
    property color headerHoverColor: UM.Theme.getColor("action_button_hovered")

    // How much spacing is needed around the popupItem
    property alias popupPadding: popup.padding

    // How much padding is needed around the header & button
    property alias headerPadding: background.padding

    // What icon should be displayed on the right.
    property alias iconSource: collapseButton.source

    property alias iconColor: collapseButton.color

    // The icon size (it's always drawn as a square)
    property alias iconSize: collapseButton.height

    // Is the "drawer" open?
    readonly property alias expanded: popup.visible

    property alias expandedHighlightColor: expandedHighlight.color

    function togglePopup()
    {
        if(popup.visible)
        {
            popup.close()
        }
        else
        {
            popup.open()
        }
    }

    onPopupItemChanged:
    {
        // Since we want the size of the popup to be set by the size of the content,
        // we need to do it like this.
        popup.width = popupItem.width + 2 * popup.padding
        popup.height = popupItem.height + 2 * popup.padding
        popup.contentItem = popupItem
    }

    Connections
    {
        // Since it could be that the popup is dynamically populated, we should also take these changes into account.
        target: popupItem
        onWidthChanged: popup.width = popupItem.width + 2 * popup.padding
        onHeightChanged: popup.height = popupItem.height + 2 * popup.padding
    }

    implicitHeight: 100 * screenScaleFactor
    implicitWidth: 400 * screenScaleFactor
    Rectangle
    {
        id: background
        property real padding: UM.Theme.getSize("default_margin").width

        color: headerBackgroundColor
        anchors.fill: parent

        Loader
        {
            id: headerItemLoader
            anchors
            {
                left: parent.left
                right: collapseButton.visible ? collapseButton.left : parent.right
                top: parent.top
                bottom: parent.bottom
                margins: background.padding
            }
        }

        // A highlight that is shown when the popup is expanded
        Rectangle
        {
            id: expandedHighlight
            width: parent.width
            height: UM.Theme.getSize("thick_lining").height
            color: UM.Theme.getColor("primary")
            visible: expanded
            anchors.bottom: parent.bottom
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
            width: height
            height: 0.2 * base.height
            color: "black"
        }

        MouseArea
        {
            id: mouseArea
            anchors.fill: parent
            onClicked: togglePopup()
            hoverEnabled: true
            onEntered: background.color = headerHoverColor
            onExited: background.color = headerBackgroundColor
        }
    }

    Popup
    {
        id: popup

        // Ensure that the popup is located directly below the headerItem
        y: headerItemLoader.height + 2 * background.padding

        // Make the popup right aligned with the rest. The 3x padding is due to left, right and padding between
        // the button & text.
        x: -width + collapseButton.width + headerItemLoader.width + 3 * background.padding
        padding: UM.Theme.getSize("default_margin").width
        closePolicy: Popup.CloseOnPressOutsideParent

        background: Rectangle
        {
            color: popupBackgroundColor
            border.width: popupBorderWidth
            border.color: popupBorderColor
        }
    }
}
