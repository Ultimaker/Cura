import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.4
import QtGraphicalEffects 1.0
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1
import UM 1.3 as UM

Item {
    id: root;
    property var printJob: null;

    Button {
        id: button;
        background: Rectangle {
            color: UM.Theme.getColor("viewport_background");
            height: button.height;
            opacity: button.down || button.hovered ? 1 : 0;
            radius: 0.5 * width;
            width: button.width;
        }
        contentItem: Label {
            color: UM.Theme.getColor("monitor_tab_text_inactive");
            font.pixelSize: 25;
            horizontalAlignment: Text.AlignHCenter;
            text: button.text;
            verticalAlignment: Text.AlignVCenter;
        }
        height: width;
        hoverEnabled: true;
        onClicked: parent.switchPopupState();
        text: "\u22EE"; //Unicode; Three stacked points.
        width: 35;
    }

    Popup {
        id: popup;
        clip: true;
        closePolicy: Popup.CloseOnPressOutside;
        height: contentItem.height + 2 * padding;
        padding: 5 * screenScaleFactor; // Because shadow
        transformOrigin: Popup.Top;
        visible: false;
        width: 182 * screenScaleFactor;
        x: (button.width - width) + 26 * screenScaleFactor;
        y: button.height + 5 * screenScaleFactor; // Because shadow
        contentItem: Item {
            width: popup.width
            height: childrenRect.height + 36 * screenScaleFactor
            anchors.topMargin: 10 * screenScaleFactor
            anchors.bottomMargin: 10 * screenScaleFactor
            Button {
                id: sendToTopButton
                text: catalog.i18nc("@label", "Move to top")
                onClicked:
                {
                    sendToTopConfirmationDialog.visible = true;
                    popup.close();
                }
                width: parent.width
                enabled: printJob ? OutputDevice.queuedPrintJobs[0].key != printJob.key : false;
                visible: enabled
                anchors.top: parent.top
                anchors.topMargin: 18 * screenScaleFactor
                height: visible ? 39 * screenScaleFactor : 0 * screenScaleFactor
                hoverEnabled: true
                background: Rectangle
                {
                    opacity: sendToTopButton.down || sendToTopButton.hovered ? 1 : 0
                    color: UM.Theme.getColor("viewport_background")
                }
                contentItem: Label
                {
                    text: sendToTopButton.text
                    horizontalAlignment: Text.AlignLeft
                    verticalAlignment: Text.AlignVCenter
                }
            }

            MessageDialog
            {
                id: sendToTopConfirmationDialog
                title: catalog.i18nc("@window:title", "Move print job to top")
                icon: StandardIcon.Warning
                text: printJob ? catalog.i18nc("@label %1 is the name of a print job.", "Are you sure you want to move %1 to the top of the queue?").arg(printJob.name) : "";
                standardButtons: StandardButton.Yes | StandardButton.No
                Component.onCompleted: visible = false
                onYes: {
                    if (printJob) {
                        OutputDevice.sendJobToTop(printJob.key)
                    }
                }
            }

            Button
            {
                id: deleteButton
                text: catalog.i18nc("@label", "Delete")
                onClicked:
                {
                    deleteConfirmationDialog.visible = true;
                    popup.close();
                }
                width: parent.width
                height: 39 * screenScaleFactor
                anchors.top: sendToTopButton.bottom
                hoverEnabled: true
                background: Rectangle
                {
                    opacity: deleteButton.down || deleteButton.hovered ? 1 : 0
                    color: UM.Theme.getColor("viewport_background")
                }
                contentItem: Label
                {
                    text: deleteButton.text
                    horizontalAlignment: Text.AlignLeft
                    verticalAlignment: Text.AlignVCenter
                }
            }

            MessageDialog
            {
                id: deleteConfirmationDialog
                title: catalog.i18nc("@window:title", "Delete print job")
                icon: StandardIcon.Warning
                text: printJob ? catalog.i18nc("@label %1 is the name of a print job.", "Are you sure you want to delete %1?").arg(printJob.name) : "";
                standardButtons: StandardButton.Yes | StandardButton.No
                Component.onCompleted: visible = false
                onYes: OutputDevice.deleteJobFromQueue(printJob.key)
            }
        }

        background: Item
        {
            width: popup.width
            height: popup.height

            DropShadow
            {
                anchors.fill: pointedRectangle
                radius: 5
                color: "#3F000000"  // 25% shadow
                source: pointedRectangle
                transparentBorder: true
                verticalOffset: 2
            }

            Item
            {
                id: pointedRectangle
                width: parent.width - 10 * screenScaleFactor // Because of the shadow
                height: parent.height - 10 * screenScaleFactor // Because of the shadow
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.verticalCenter: parent.verticalCenter

                Rectangle
                {
                    id: point
                    height: 14 * screenScaleFactor
                    width: 14 * screenScaleFactor
                    color: UM.Theme.getColor("setting_control")
                    transform: Rotation { angle: 45}
                    anchors.right: bloop.right
                    anchors.rightMargin: 24
                    y: 1
                }

                Rectangle
                {
                    id: bloop
                    color: UM.Theme.getColor("setting_control")
                    width: parent.width
                    anchors.top: parent.top
                    anchors.topMargin: 8 * screenScaleFactor // Because of the shadow + point
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 8 * screenScaleFactor // Because of the shadow
                }
            }
        }

        exit: Transition
        {
            NumberAnimation { property: "visible"; duration: 75; }
        }
        enter: Transition
        {
            NumberAnimation { property: "visible"; duration: 75; }
        }

        onClosed: visible = false
        onOpened: visible = true
    }

    // Utils
    function switchPopupState() {
        popup.visible ? popup.close() : popup.open()
    }
}
