import QtQuick 2.3
import QtQuick.Dialogs 1.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.3
import QtGraphicalEffects 1.0

import QtQuick.Controls 2.0 as Controls2

import UM 1.3 as UM
import Cura 1.0 as Cura


Component
{
    Rectangle
    {
        id: base
        property var lineColor: "#DCDCDC" // TODO: Should be linked to theme.

        property var cornerRadius: 4 * screenScaleFactor // TODO: Should be linked to theme.
        visible: OutputDevice != null
        anchors.fill: parent
        color: "white"

        UM.I18nCatalog
        {
            id: catalog
            name: "cura"
        }

        Label
        {
            id: printingLabel
            font: UM.Theme.getFont("large")
            anchors
            {
                margins: 2 * UM.Theme.getSize("default_margin").width
                leftMargin: 4 * UM.Theme.getSize("default_margin").width
                top: parent.top
                left: parent.left
                right: parent.right
            }

            text: catalog.i18nc("@label", "Printing")
            elide: Text.ElideRight
        }

        Label
        {
            id: managePrintersLabel
            anchors.rightMargin: 4 * UM.Theme.getSize("default_margin").width
            anchors.right: printerScrollView.right
            anchors.bottom: printingLabel.bottom
            text: catalog.i18nc("@label link to connect manager", "Manage printers")
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("primary")
            linkColor: UM.Theme.getColor("primary")
        }

        MouseArea
        {
            anchors.fill: managePrintersLabel
            hoverEnabled: true
            onClicked: Cura.MachineManager.printerOutputDevices[0].openPrinterControlPanel()
            onEntered: managePrintersLabel.font.underline = true
            onExited: managePrintersLabel.font.underline = false
        }

        ScrollView
        {
            id: printerScrollView
            anchors
            {
                top: printingLabel.bottom
                left: parent.left
                right: parent.right
                topMargin: UM.Theme.getSize("default_margin").height
                bottom: parent.bottom
                bottomMargin: UM.Theme.getSize("default_margin").height
            }

            style: UM.Theme.styles.scrollview

            ListView
            {
                anchors
                {
                    top: parent.top
                    bottom: parent.bottom
                    left: parent.left
                    right: parent.right
                    leftMargin: 2 * UM.Theme.getSize("default_margin").width
                    rightMargin: 2 * UM.Theme.getSize("default_margin").width
                }
                spacing: UM.Theme.getSize("default_margin").height -10
                model: OutputDevice.printers

                delegate: Item
                {
                    width: parent.width
                    height: base.height + 2 * base.shadowRadius // To ensure that the shadow doesn't get cut off.
                    Rectangle
                    {
                        width: parent.width - 2 * shadowRadius
                        height: childrenRect.height + UM.Theme.getSize("default_margin").height
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.verticalCenter: parent.verticalCenter
                        id: base
                        property var shadowRadius: 5
                        property var collapsed: true

                        layer.enabled: true
                        layer.effect: DropShadow
                        {
                            radius: base.shadowRadius
                            verticalOffset: 2
                            color: "#3F000000"  // 25% shadow
                        }

                        Item
                        {
                            id: printerInfo
                            height: machineIcon.height
                            anchors
                            {
                                top: parent.top
                                left: parent.left
                                right: parent.right
                                margins: UM.Theme.getSize("default_margin").width
                            }

                            MouseArea
                            {
                                anchors.fill: parent
                                onClicked: base.collapsed = !base.collapsed
                            }

                            Item
                            {
                                id: machineIcon
                                // Yeah, this is hardcoded now, but I can't think of a good way to fix this.
                                // The UI is going to get another update soon, so it's probably not worth the effort...
                                width: 58
                                height: 58
                                anchors.top: parent.top
                                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                                anchors.left: parent.left

                                UM.RecolorImage
                                {
                                    anchors.centerIn: parent
                                    source:
                                    {
                                        switch(modelData.type)
                                        {
                                            case "Ultimaker 3":
                                                return "../svg/UM3-icon.svg"
                                            case "Ultimaker 3 Extended":
                                                return "../svg/UM3x-icon.svg"
                                            case "Ultimaker S5":
                                                return "../svg/UMs5-icon.svg"
                                        }
                                    }
                                    width: sourceSize.width
                                    height: sourceSize.height

                                    color:
                                    {
                                        if(modelData.state == "disabled")
                                        {
                                            return UM.Theme.getColor("setting_control_disabled")
                                        }

                                        if(modelData.activePrintJob != undefined)
                                        {
                                            return UM.Theme.getColor("primary")
                                        }

                                        return UM.Theme.getColor("setting_control_disabled")
                                    }
                                }
                            }
                            Item
                            {
                                height: childrenRect.height
                                anchors
                                {
                                    right: collapseIcon.left
                                    rightMargin: UM.Theme.getSize("default_margin").width
                                    left: machineIcon.right
                                    leftMargin: UM.Theme.getSize("default_margin").width

                                    verticalCenter: machineIcon.verticalCenter
                                }

                                Label
                                {
                                    id: machineNameLabel
                                    text: modelData.name
                                    width: parent.width
                                    elide: Text.ElideRight
                                    font: UM.Theme.getFont("default_bold")
                                }

                                Label
                                {
                                    id: activeJobLabel
                                    text:
                                    {
                                        if (modelData.state == "disabled")
                                        {
                                            return catalog.i18nc("@label", "Not available")
                                        } else if (modelData.state == "unreachable")
                                        {
                                            return catalog.i18nc("@label", "Unreachable")
                                        }
                                        if (modelData.activePrintJob != null)
                                        {
                                            return modelData.activePrintJob.name
                                        }
                                        return catalog.i18nc("@label", "Available")
                                    }
                                    anchors.top: machineNameLabel.bottom
                                    width: parent.width
                                    elide: Text.ElideRight
                                    font: UM.Theme.getFont("default")
                                    opacity: 0.6
                                }
                            }

                            UM.RecolorImage
                            {
                                id: collapseIcon
                                width: 15
                                height: 15
                                sourceSize.width: width
                                sourceSize.height: height
                                source: base.collapsed ?  UM.Theme.getIcon("arrow_left") : UM.Theme.getIcon("arrow_bottom")
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.right: parent.right
                                anchors.rightMargin: UM.Theme.getSize("default_margin").width
                                color: "black"
                            }
                        }

                        Item
                        {
                            id: detailedInfo
                            property var printJob: modelData.activePrintJob
                            visible: height == childrenRect.height
                            anchors.top: printerInfo.bottom
                            width: parent.width
                            height: !base.collapsed ? childrenRect.height : 0
                            opacity: visible ? 1 : 0
                            Behavior on height { NumberAnimation { duration: 100 } }
                            Behavior on opacity { NumberAnimation { duration: 100 } }
                            Rectangle
                            {
                                id: topSpacer
                                color: UM.Theme.getColor("viewport_background")
                                height: 2
                                anchors
                                {
                                    left: parent.left
                                    right: parent.right
                                    margins: UM.Theme.getSize("default_margin").width
                                    top: parent.top
                                    topMargin: UM.Theme.getSize("default_margin").width
                                }
                            }
                            PrinterFamilyPill
                            {
                                id: printerFamilyPill
                                color: UM.Theme.getColor("viewport_background")
                                anchors.top: topSpacer.bottom
                                anchors.topMargin: 2 * UM.Theme.getSize("default_margin").height
                                text: modelData.type
                                anchors.left: parent.left
                                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                                padding: 3
                            }
                            Row
                            {
                                id: extrudersInfo
                                anchors.top: printerFamilyPill.bottom
                                anchors.topMargin: 2 * UM.Theme.getSize("default_margin").height
                                anchors.left: parent.left
                                anchors.leftMargin: 2 * UM.Theme.getSize("default_margin").width
                                anchors.right: parent.right
                                anchors.rightMargin: 2 * UM.Theme.getSize("default_margin").width
                                height: childrenRect.height
                                spacing: UM.Theme.getSize("default_margin").width

                                PrintCoreConfiguration
                                {
                                    id: leftExtruderInfo
                                    width: Math.round(parent.width  / 2)
                                    printCoreConfiguration: modelData.printerConfiguration.extruderConfigurations[0]
                                }

                                PrintCoreConfiguration
                                {
                                    id: rightExtruderInfo
                                    width: Math.round(parent.width / 2)
                                    printCoreConfiguration: modelData.printerConfiguration.extruderConfigurations[1]
                                }
                            }

                            Rectangle
                            {
                                id: jobSpacer
                                color: UM.Theme.getColor("viewport_background")
                                height: 2
                                anchors
                                {
                                    left: parent.left
                                    right: parent.right
                                    margins: UM.Theme.getSize("default_margin").width
                                    top: extrudersInfo.bottom
                                    topMargin: 2 * UM.Theme.getSize("default_margin").height
                                }
                            }

                            Item
                            {
                                id: jobInfo
                                property var showJobInfo: modelData.activePrintJob != null && modelData.activePrintJob.state != "queued"

                                anchors.top: jobSpacer.bottom
                                anchors.topMargin: 2 * UM.Theme.getSize("default_margin").height
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.margins: UM.Theme.getSize("default_margin").width
                                anchors.leftMargin: 2 * UM.Theme.getSize("default_margin").width
                                height: showJobInfo ? childrenRect.height + 2 * UM.Theme.getSize("default_margin").height: 0
                                visible: showJobInfo
                                Label
                                {
                                    id: printJobName
                                    text: modelData.activePrintJob != null ? modelData.activePrintJob.name : ""
                                    font: UM.Theme.getFont("default_bold")
                                    anchors.left: parent.left
                                    anchors.right: contextButton.left
                                    anchors.rightMargin: UM.Theme.getSize("default_margin").width
                                    elide: Text.ElideRight
                                }
                                Label
                                {
                                    id: ownerName
                                    anchors.top: printJobName.bottom
                                    text: modelData.activePrintJob != null ? modelData.activePrintJob.owner : ""
                                    font: UM.Theme.getFont("default")
                                    opacity: 0.6
                                    width: parent.width
                                    elide: Text.ElideRight
                                }

                                function switchPopupState()
                                {
                                    if (popup.visible)
                                    {
                                        popup.close()
                                    }
                                    else
                                    {
                                        popup.open()
                                    }
                                }

                                Controls2.Button
                                {
                                    id: contextButton
                                    text: "\u22EE" //Unicode; Three stacked points.
                                    font.pixelSize: 25
                                    width: 35
                                    height: width
                                    anchors
                                    {
                                        right: parent.right
                                        top: parent.top
                                    }
                                    hoverEnabled: true

                                    background: Rectangle
                                    {
                                        opacity: contextButton.down || contextButton.hovered ? 1 : 0
                                        width: contextButton.width
                                        height: contextButton.height
                                        radius: 0.5 * width
                                        color: UM.Theme.getColor("viewport_background")
                                    }

                                    onClicked: parent.switchPopupState()
                                }

                                Controls2.Popup
                                {
                                    // TODO Change once updating to Qt5.10 - The 'opened' property is in 5.10 but the behavior is now implemented with the visible property
                                    id: popup
                                    clip: true
                                    closePolicy: Controls2.Popup.CloseOnPressOutsideParent
                                    x: parent.width - width
                                    y: contextButton.height
                                    width: 160
                                    height: contentItem.height + 2 * padding
                                    visible: false

                                    transformOrigin: Controls2.Popup.Top
                                    contentItem: Item
                                    {
                                        width: popup.width - 2 * popup.padding
                                        height: childrenRect.height + 15
                                        Controls2.Button
                                        {
                                            id: pauseButton
                                            text: modelData.activePrintJob != null && modelData.activePrintJob.state == "paused" ? catalog.i18nc("@label", "Resume") : catalog.i18nc("@label", "Pause")
                                            onClicked:
                                            {
                                                if(modelData.activePrintJob.state == "paused")
                                                {
                                                    modelData.activePrintJob.setState("print")
                                                }
                                                else if(modelData.activePrintJob.state == "printing")
                                                {
                                                    modelData.activePrintJob.setState("pause")
                                                }
                                                popup.close()
                                            }
                                            width: parent.width
                                            enabled: modelData.activePrintJob != null && ["paused", "printing"].indexOf(modelData.activePrintJob.state) >= 0
                                            anchors.top: parent.top
                                            anchors.topMargin: 10
                                            hoverEnabled: true
                                            background:  Rectangle
                                            {
                                                opacity: pauseButton.down || pauseButton.hovered ? 1 : 0
                                                color: UM.Theme.getColor("viewport_background")
                                            }
                                        }

                                        Controls2.Button
                                        {
                                            id: abortButton
                                            text: catalog.i18nc("@label", "Abort")
                                            onClicked:
                                            {
                                                abortConfirmationDialog.visible = true;
                                                popup.close();
                                            }
                                            width: parent.width
                                            anchors.top: pauseButton.bottom
                                            hoverEnabled: true
                                            enabled: modelData.activePrintJob != null && ["paused", "printing", "pre_print"].indexOf(modelData.activePrintJob.state) >= 0
                                            background: Rectangle
                                            {
                                                opacity: abortButton.down || abortButton.hovered ? 1 : 0
                                                color: UM.Theme.getColor("viewport_background")
                                            }
                                        }

                                        MessageDialog
                                        {
                                            id: abortConfirmationDialog
                                            title: catalog.i18nc("@window:title", "Abort print")
                                            icon: StandardIcon.Warning
                                            text: catalog.i18nc("@label %1 is the name of a print job.", "Are you sure you want to abort %1?").arg(modelData.activePrintJob.name)
                                            standardButtons: StandardButton.Yes | StandardButton.No
                                            Component.onCompleted: visible = false
                                            onYes: modelData.activePrintJob.setState("abort")
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
                                            width: parent.width -10
                                            height: parent.height -10
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            anchors.verticalCenter: parent.verticalCenter

                                            Rectangle
                                            {
                                                id: point
                                                height: 13
                                                width: 13
                                                color: UM.Theme.getColor("setting_control")
                                                transform: Rotation { angle: 45}
                                                anchors.right: bloop.right
                                                y: 1
                                            }

                                            Rectangle
                                            {
                                                id: bloop
                                                color: UM.Theme.getColor("setting_control")
                                                width: parent.width
                                                anchors.top: parent.top
                                                anchors.topMargin: 10
                                                anchors.bottom: parent.bottom
                                                anchors.bottomMargin: 5
                                            }
                                        }
                                    }

                                    exit: Transition
                                    {
                                        // This applies a default NumberAnimation to any changes a state change makes to x or y properties
                                        NumberAnimation { property: "visible"; duration: 75; }
                                    }
                                    enter: Transition
                                    {
                                        // This applies a default NumberAnimation to any changes a state change makes to x or y properties
                                        NumberAnimation { property: "visible"; duration: 75; }
                                    }

                                    onClosed: visible = false
                                    onOpened: visible = true
                                }

                                Image
                                {
                                    id: printJobPreview
                                    source: modelData.activePrintJob != null ? modelData.activePrintJob.previewImageUrl : ""
                                    anchors.top: ownerName.bottom
                                    anchors.horizontalCenter: parent.horizontalCenter
                                    width: parent.width / 2
                                    height: width
                                    opacity:
                                    {
                                        if(modelData.activePrintJob == null)
                                        {
                                            return 1.0
                                        }

                                        switch(modelData.activePrintJob.state)
                                        {
                                            case "wait_cleanup":
                                            case "wait_user_action":
                                            case "paused":
                                                return 0.5
                                            default:
                                                return 1.0
                                        }
                                    }


                                }

                                UM.RecolorImage
                                {
                                    id: statusImage
                                    anchors.centerIn: printJobPreview
                                    source:
                                    {
                                        if(modelData.activePrintJob == null)
                                        {
                                            return ""
                                        }
                                        switch(modelData.activePrintJob.state)
                                        {
                                            case "paused":
                                                return "../svg/paused-icon.svg"
                                            case "wait_cleanup":
                                                if(modelData.activePrintJob.timeElapsed < modelData.activePrintJob.timeTotal)
                                                {
                                                    return "../svg/aborted-icon.svg"
                                                }
                                                return "../svg/approved-icon.svg"
                                            case "wait_user_action":
                                                return "../svg/aborted-icon.svg"
                                            default:
                                                return ""
                                        }
                                    }
                                    visible: source != ""
                                    width: 0.5 * printJobPreview.width
                                    height: 0.5 * printJobPreview.height
                                    sourceSize.width: width
                                    sourceSize.height: height
                                    color: "black"
                                }

                                Rectangle
                                {
                                    id: showCameraIcon
                                    width: 35 * screenScaleFactor
                                    height: width
                                    radius: 0.5 * width
                                    anchors.left: parent.left
                                    anchors.bottom: printJobPreview.bottom
                                    color: UM.Theme.getColor("setting_control_border_highlight")
                                    Image
                                    {
                                        width: parent.width
                                        height: width
                                        anchors.right: parent.right
                                        anchors.rightMargin: parent.rightMargin
                                        source: "../svg/camera-icon.svg"
                                    }
                                    MouseArea
                                    {
                                        anchors.fill:parent
                                        onClicked:
                                        {
                                            OutputDevice.setActiveCamera(modelData.camera)
                                        }
                                    }
                                }
                            }
                        }

                        ProgressBar
                        {
                            property var progress:
                            {
                                if(modelData.activePrintJob == null)
                                {
                                    return 0
                                }
                                var result =  modelData.activePrintJob.timeElapsed / modelData.activePrintJob.timeTotal
                                if(result > 1.0)
                                {
                                    result = 1.0
                                }
                                return result
                            }

                            id: jobProgressBar
                            width: parent.width
                            value: progress
                            anchors.top: detailedInfo.bottom
                            anchors.topMargin: UM.Theme.getSize("default_margin").height

                            visible: modelData.activePrintJob != null && modelData.activePrintJob != undefined

                            style: ProgressBarStyle
                            {
                                property var progressText:
                                {
                                    if(modelData.activePrintJob == null)
                                    {
                                        return ""
                                    }

                                    switch(modelData.activePrintJob.state)
                                    {
                                        case "wait_cleanup":
                                            if(modelData.activePrintJob.timeTotal > modelData.activePrintJob.timeElapsed)
                                            {
                                                return catalog.i18nc("@label:status", "Aborted")
                                            }
                                            return catalog.i18nc("@label:status", "Finished")
                                        case "pre_print":
                                        case "sent_to_printer":
                                            return catalog.i18nc("@label:status", "Preparing")
                                        case "aborted":
                                        case "wait_user_action":
                                            return catalog.i18nc("@label:status", "Aborted")
                                        case "pausing":
                                            return catalog.i18nc("@label:status", "Pausing")
                                        case "paused":
                                            return catalog.i18nc("@label:status", "Paused")
                                        case "resuming":
                                            return catalog.i18nc("@label:status", "Resuming")
                                        case "queued":
                                            return catalog.i18nc("@label:status", "Action required")
                                        default:
                                            OutputDevice.formatDuration(modelData.activePrintJob.timeTotal - modelData.activePrintJob.timeElapsed)
                                    }
                                }

                                background: Rectangle
                                {
                                    implicitWidth: 100
                                    implicitHeight: visible ? 24 : 0
                                    color: UM.Theme.getColor("viewport_background")
                                }

                                progress: Rectangle
                                {
                                    color: UM.Theme.getColor("primary")
                                    id: progressItem
                                    function getTextOffset()
                                    {
                                        if(progressItem.width + progressLabel.width < control.width)
                                        {
                                            return progressItem.width + UM.Theme.getSize("default_margin").width
                                        }
                                        else
                                        {
                                            return progressItem.width - progressLabel.width - UM.Theme.getSize("default_margin").width
                                        }
                                    }

                                    Label
                                    {
                                        id: progressLabel
                                        anchors.left: parent.left
                                        anchors.leftMargin: getTextOffset()
                                        text: progressText
                                        anchors.verticalCenter: parent.verticalCenter
                                        color: progressItem.width + progressLabel.width < control.width ? "black" : "white"
                                        width: contentWidth
                                        font: UM.Theme.getFont("default")
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
