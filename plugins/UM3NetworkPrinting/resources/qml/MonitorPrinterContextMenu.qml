// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Controls 2.0
import QtQuick.Dialogs 1.1
import UM 1.3 as UM

/**
 * A MonitorInfoBlurb is an extension of the GenericPopUp used to show static information (vs. interactive context
 * menus). It accepts some text (text), an item to link to to (target), and a specification of which side of the target
 * to appear on (direction). It also sets the GenericPopUp's color to black, to differentiate itself from a menu.
 */
Item
{
    property alias target: popUp.target

    property var printJob: null

    GenericPopUp
    {
        id: popUp

        // If the pop-up won't fit in the window, flip it
        direction:
        {
            var availableSpace = monitorFrame.height
            var targetPosition = target.mapToItem(null, 0, 0)
            var requiredSpace = targetPosition.y + target.height + contentWrapper.implicitHeight
            return requiredSpace < availableSpace ? "top" : "bottom"
        }

        // Use dark grey for info blurbs and white for context menus
        color: "#ffffff" // TODO: Theme!

        contentItem: Item
        {
            id: contentWrapper
            implicitWidth: childrenRect.width
            implicitHeight: innerLabel.contentHeight
            Label
            {
                id: innerLabel
                text: "The future of context menus starts here!"
                wrapMode: Text.WordWrap
                width: 182 * screenScaleFactor // TODO: Theme!
                color: "white" // TODO: Theme!
                font: UM.Theme.getFont("default")
            }
        }
    }

    MessageDialog {
        id: sendToTopConfirmationDialog
        Component.onCompleted: visible = false
        icon: StandardIcon.Warning
        onYes: OutputDevice.sendJobToTop(printJob.key)
        standardButtons: StandardButton.Yes | StandardButton.No
        text: printJob && printJob.name ? catalog.i18nc("@label %1 is the name of a print job.", "Are you sure you want to move %1 to the top of the queue?").arg(printJob.name) : ""
        title: catalog.i18nc("@window:title", "Move print job to top")
    }

    MessageDialog {
        id: deleteConfirmationDialog
        Component.onCompleted: visible = false
        icon: StandardIcon.Warning
        onYes: OutputDevice.deleteJobFromQueue(printJob.key)
        standardButtons: StandardButton.Yes | StandardButton.No
        text: printJob && printJob.name ? catalog.i18nc("@label %1 is the name of a print job.", "Are you sure you want to delete %1?").arg(printJob.name) : ""
        title: catalog.i18nc("@window:title", "Delete print job")
    }

    MessageDialog {
        id: abortConfirmationDialog
        Component.onCompleted: visible = false
        icon: StandardIcon.Warning
        onYes: printJob.setState("abort")
        standardButtons: StandardButton.Yes | StandardButton.No
        text: printJob && printJob.name ? catalog.i18nc("@label %1 is the name of a print job.", "Are you sure you want to abort %1?").arg(printJob.name) : ""
        title: catalog.i18nc("@window:title", "Abort print")
    }

    function switchPopupState() {
        popUp.visible ? popUp.close() : popUp.open()
    }
    function open() {
        popUp.open()
    }
    function close() {
        popUp.close()
    }
}
