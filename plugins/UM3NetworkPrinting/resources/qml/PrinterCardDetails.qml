import QtQuick 2.3
import QtQuick.Dialogs 1.1
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.3
import QtGraphicalEffects 1.0
import QtQuick.Controls 1.4 as LegacyControls
import UM 1.3 as UM

Item {
    id: root;

    property var printer: null;
    property var printJob: printer.activePrintJob;
    property var collapsed: true;

    Behavior on height { NumberAnimation { duration: 100 } }
    Behavior on opacity { NumberAnimation { duration: 100 } }

    width: parent.width;
    height: collapsed ? 0 : childrenRect.height;
    opacity: collapsed ? 0 : 1;

    Column {
        height: childrenRect.height;
        width: parent.width;

        spacing: UM.Theme.getSize("default_margin").height;

        HorizontalLine { enabled: printer.state !== "disabled" }

        PrinterInfoBlock {
            printer: root.printer;
            printJob: root.printer.activePrintJob;
        }

        HorizontalLine { enabled: printer.state !== "disabled" }

        Rectangle {
            color: "orange";
            width: parent.width;
            height: 100;
        }

        Item {
            id: jobInfoSection;

            property var job: root.printer ? root.printer.activePrintJob : null;

            Component.onCompleted: {
                console.log(job)
            }
            height: visible ? childrenRect.height + 2 * UM.Theme.getSize("default_margin").height : 0;
            width: parent.width;
            visible: job && job.state != "queued";

            anchors.left: parent.left;
            // anchors.right: contextButton.left;
            // anchors.rightMargin: UM.Theme.getSize("default_margin").width;

            Label {
                id: printJobName;
                elide: Text.ElideRight;
                font: UM.Theme.getFont("default_bold");
                text: job ? job.name : "";
            }

            Label {
                id: ownerName;
                anchors.top: job.bottom;
                elide: Text.ElideRight;
                font: UM.Theme.getFont("default");
                opacity: 0.6;
                text: job ? job.owner : "";
                width: parent.width;
            }
        }
    }
}


//     Item {
//         id: jobInfo;
//         property var showJobInfo: {
//             return printer.activePrintJob != null && printer.activePrintJob.state != "queued"
//         }

//         // anchors {
//         //     top: jobSpacer.bottom
//         //     topMargin: 2 * UM.Theme.getSize("default_margin").height
//         //     left: parent.left
//         //     right: parent.right
//         //     margins: UM.Theme.getSize("default_margin").width
//         //     leftMargin: 2 * UM.Theme.getSize("default_margin").width
//         // }

//         height: showJobInfo ? childrenRect.height + 2 * UM.Theme.getSize("default_margin").height : 0;
//         visible: showJobInfo;


//         function switchPopupState()
//         {
//             popup.visible ? popup.close() : popup.open()
//         }

//         Button
//         {
//             id: contextButton
//             text: "\u22EE" //Unicode; Three stacked points.
//             width: 35
//             height: width
//             anchors
//             {
//                 right: parent.right
//                 top: parent.top
//             }
//             hoverEnabled: true

//             background: Rectangle
//             {
//                 opacity: contextButton.down || contextButton.hovered ? 1 : 0
//                 width: contextButton.width
//                 height: contextButton.height
//                 radius: 0.5 * width
//                 color: UM.Theme.getColor("viewport_background")
//             }
//             contentItem: Label
//             {
//                 text: contextButton.text
//                 color: UM.Theme.getColor("monitor_tab_text_inactive")
//                 font.pixelSize: 25
//                 verticalAlignment: Text.AlignVCenter
//                 horizontalAlignment: Text.AlignHCenter
//             }

//             onClicked: parent.switchPopupState()
//         }

//         Popup
//         {
//             // TODO Change once updating to Qt5.10 - The 'opened' property is in 5.10 but the behavior is now implemented with the visible property
//             id: popup
//             clip: true
//             closePolicy: Popup.CloseOnPressOutside
//             x: (parent.width - width) + 26 * screenScaleFactor
//             y: contextButton.height - 5 * screenScaleFactor // Because shadow
//             width: 182 * screenScaleFactor
//             height: contentItem.height + 2 * padding
//             visible: false
//             padding: 5 * screenScaleFactor // Because shadow

//             transformOrigin: Popup.Top
//             contentItem: Item
//             {
//                 width: popup.width
//                 height: childrenRect.height + 36 * screenScaleFactor
//                 anchors.topMargin: 10 * screenScaleFactor
//                 anchors.bottomMargin: 10 * screenScaleFactor
//                 Button
//                 {
//                     id: pauseButton
//                     text: printer.activePrintJob != null && printer.activePrintJob.state == "paused" ? catalog.i18nc("@label", "Resume") : catalog.i18nc("@label", "Pause")
//                     onClicked:
//                     {
//                         if(printer.activePrintJob.state == "paused")
//                         {
//                             printer.activePrintJob.setState("print")
//                         }
//                         else if(printer.activePrintJob.state == "printing")
//                         {
//                             printer.activePrintJob.setState("pause")
//                         }
//                         popup.close()
//                     }
//                     width: parent.width
//                     enabled: printer.activePrintJob != null && ["paused", "printing"].indexOf(printer.activePrintJob.state) >= 0
//                     visible: enabled
//                     anchors.top: parent.top
//                     anchors.topMargin: 18 * screenScaleFactor
//                     height: visible ? 39 * screenScaleFactor : 0 * screenScaleFactor
//                     hoverEnabled: true
//                     background: Rectangle
//                     {
//                         opacity: pauseButton.down || pauseButton.hovered ? 1 : 0
//                         color: UM.Theme.getColor("viewport_background")
//                     }
//                     contentItem: Label
//                     {
//                         text: pauseButton.text
//                         horizontalAlignment: Text.AlignLeft
//                         verticalAlignment: Text.AlignVCenter
//                     }
//                 }

//                 Button
//                 {
//                     id: abortButton
//                     text: catalog.i18nc("@label", "Abort")
//                     onClicked:
//                     {
//                         abortConfirmationDialog.visible = true;
//                         popup.close();
//                     }
//                     width: parent.width
//                     height: 39 * screenScaleFactor
//                     anchors.top: pauseButton.bottom
//                     hoverEnabled: true
//                     enabled: printer.activePrintJob != null && ["paused", "printing", "pre_print"].indexOf(printer.activePrintJob.state) >= 0
//                     background: Rectangle
//                     {
//                         opacity: abortButton.down || abortButton.hovered ? 1 : 0
//                         color: UM.Theme.getColor("viewport_background")
//                     }
//                     contentItem: Label
//                     {
//                         text: abortButton.text
//                         horizontalAlignment: Text.AlignLeft
//                         verticalAlignment: Text.AlignVCenter
//                     }
//                 }

//                 MessageDialog
//                 {
//                     id: abortConfirmationDialog
//                     title: catalog.i18nc("@window:title", "Abort print")
//                     icon: StandardIcon.Warning
//                     text: catalog.i18nc("@label %1 is the name of a print job.", "Are you sure you want to abort %1?").arg(printer.activePrintJob.name)
//                     standardButtons: StandardButton.Yes | StandardButton.No
//                     Component.onCompleted: visible = false
//                     onYes: printer.activePrintJob.setState("abort")
//                 }
//             }

//             background: Item
//             {
//                 width: popup.width
//                 height: popup.height

//                 DropShadow
//                 {
//                     anchors.fill: pointedRectangle
//                     radius: 5
//                     color: "#3F000000"  // 25% shadow
//                     source: pointedRectangle
//                     transparentBorder: true
//                     verticalOffset: 2
//                 }

//                 Item
//                 {
//                     id: pointedRectangle
//                     width: parent.width - 10 * screenScaleFactor // Because of the shadow
//                     height: parent.height - 10 * screenScaleFactor // Because of the shadow
//                     anchors.horizontalCenter: parent.horizontalCenter
//                     anchors.verticalCenter: parent.verticalCenter

//                     Rectangle
//                     {
//                         id: point
//                         height: 14 * screenScaleFactor
//                         width: 14 * screenScaleFactor
//                         color: UM.Theme.getColor("setting_control")
//                         transform: Rotation { angle: 45}
//                         anchors.right: bloop.right
//                         anchors.rightMargin: 24
//                         y: 1
//                     }

//                     Rectangle
//                     {
//                         id: bloop
//                         color: UM.Theme.getColor("setting_control")
//                         width: parent.width
//                         anchors.top: parent.top
//                         anchors.topMargin: 8 * screenScaleFactor // Because of the shadow + point
//                         anchors.bottom: parent.bottom
//                         anchors.bottomMargin: 8 * screenScaleFactor // Because of the shadow
//                     }
//                 }
//             }

//             exit: Transition
//             {
//                 // This applies a default NumberAnimation to any changes a state change makes to x or y properties
//                 NumberAnimation { property: "visible"; duration: 75; }
//             }
//             enter: Transition
//             {
//                 // This applies a default NumberAnimation to any changes a state change makes to x or y properties
//                 NumberAnimation { property: "visible"; duration: 75; }
//             }

//             onClosed: visible = false
//             onOpened: visible = true
//         }

//         Image
//         {
//             id: printJobPreview
//             source: printer.activePrintJob != null ? printer.activePrintJob.previewImageUrl : ""
//             anchors.top: ownerName.bottom
//             anchors.horizontalCenter: parent.horizontalCenter
//             width: parent.width / 2
//             height: width
//             opacity:
//             {
//                 if(printer.activePrintJob == null)
//                 {
//                     return 1.0
//                 }

//                 switch(printer.activePrintJob.state)
//                 {
//                     case "wait_cleanup":
//                     case "wait_user_action":
//                     case "paused":
//                         return 0.5
//                     default:
//                         return 1.0
//                 }
//             }


//         }

//         UM.RecolorImage
//         {
//             id: statusImage
//             anchors.centerIn: printJobPreview
//             source:
//             {
//                 if(printer.activePrintJob == null)
//                 {
//                     return ""
//                 }
//                 switch(printer.activePrintJob.state)
//                 {
//                     case "paused":
//                         return "../svg/paused-icon.svg"
//                     case "wait_cleanup":
//                         if(printer.activePrintJob.timeElapsed < printer.activePrintJob.timeTotal)
//                         {
//                             return "../svg/aborted-icon.svg"
//                         }
//                         return "../svg/approved-icon.svg"
//                     case "wait_user_action":
//                         return "../svg/aborted-icon.svg"
//                     default:
//                         return ""
//                 }
//             }
//             visible: source != ""
//             width: 0.5 * printJobPreview.width
//             height: 0.5 * printJobPreview.height
//             sourceSize.width: width
//             sourceSize.height: height
//             color: "black"
//         }

//         CameraButton
//         {
//             id: showCameraButton
//             iconSource: "../svg/camera-icon.svg"
//             anchors
//             {
//                 left: parent.left
//                 bottom: printJobPreview.bottom
//             }
//         }
//     }
// }