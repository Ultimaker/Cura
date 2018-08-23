import QtQuick 2.3
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.3
import QtGraphicalEffects 1.0


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
        color: UM.Theme.getColor("viewport_background")

        UM.I18nCatalog
        {
            id: catalog
            name: "cura"
        }

        Label
        {
            id: activePrintersLabel
            font: UM.Theme.getFont("large")
            anchors
            {
                margins: UM.Theme.getSize("default_margin").width
                top: parent.top
                left: parent.left
                right: parent.right
            }

            text: OutputDevice.name
            elide: Text.ElideRight
        }


        ScrollView
        {
            anchors
            {
                top: activePrintersLabel.bottom
                left: parent.left
                right: parent.right
                margins: UM.Theme.getSize("default_margin").width
                bottom: parent.bottom
            }
            ListView
            {
                anchors.fill: parent
                spacing: UM.Theme.getSize("default_margin").height
                displayMarginBeginning: 2
                model: OutputDevice.printers
                delegate: Rectangle
                {
                    width: parent.width - 2 * shadowRadius
                    height: childrenRect.height + UM.Theme.getSize("default_margin").height
                    anchors.horizontalCenter: parent.horizontalCenter
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

                        Rectangle
                        {
                            id: machineIcon
                            anchors.top: parent.top
                            width: 50
                            height: 50
                            color: modelData.activePrintJob != undefined ? UM.Theme.getColor("primary") : UM.Theme.getColor("setting_control_disabled")
                        }

                        Label
                        {
                            id: machineNameLabel
                            text: modelData.name
                            anchors.top: machineIcon.top
                            anchors.left: machineIcon.right
                            anchors.leftMargin: UM.Theme.getSize("default_margin").width
                            anchors.right: collapseIcon.left
                            anchors.rightMargin: UM.Theme.getSize("default_margin").width
                            elide: Text.ElideRight
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

                        Label
                        {
                            id: activeJobLabel
                            text: modelData.activePrintJob != null ? modelData.activePrintJob.name : "waiting"
                            anchors.top: machineNameLabel.bottom
                            anchors.left: machineNameLabel.left
                            anchors.right: collapseIcon.left
                            anchors.rightMargin: UM.Theme.getSize("default_margin").width
                            elide: Text.ElideRight
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
                        Behavior on opacity { NumberAnimation { duration: 50 } }
                        Rectangle
                        {
                            id: topSpacer
                            color: "grey"
                            height: 1
                            anchors
                            {
                                left: parent.left
                                right: parent.right
                                margins: UM.Theme.getSize("default_margin").width
                                top: parent.top
                            }
                        }

                        Row
                        {
                            id: extrudersInfo
                            anchors.top: topSpacer.bottom
                            anchors.topMargin : UM.Theme.getSize("default_margin").height
                            anchors.left: parent.left
                            anchors.leftMargin: UM.Theme.getSize("default_margin").width
                            anchors.right: parent.right
                            anchors.rightMargin: UM.Theme.getSize("default_margin").width
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
                            color: "grey"
                            height: 1
                            anchors
                            {
                                left: parent.left
                                right: parent.right
                                margins: UM.Theme.getSize("default_margin").width
                                top: extrudersInfo.bottom
                            }
                        }

                        Item
                        {
                            id: jobInfo
                            property var showJobInfo: modelData.activePrintJob != null && modelData.activePrintJob.state != "queued"

                            anchors.top: jobSpacer.bottom
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.margins: UM.Theme.getSize("default_margin").width
                            height: showJobInfo ? childrenRect.height + UM.Theme.getSize("default_margin").height: 0
                            visible: showJobInfo
                            Label
                            {
                                id: printJobName
                                text: modelData.activePrintJob != null ? modelData.activePrintJob.name : ""
                                font: UM.Theme.getFont("default_bold")
                            }
                            Label
                            {
                                id: ownerName
                                anchors.top: printJobName.bottom
                                text: modelData.activePrintJob != null ? modelData.activePrintJob.owner : ""
                            }

                            Image
                            {
                                id: printJobPreview
                                source: modelData.activePrintJob != null ? modelData.activePrintJob.preview_image_url : ""
                                anchors.top: ownerName.bottom
                                anchors.horizontalCenter: parent.horizontalCenter
                                width: parent.width / 3
                                height: width
                            }

                            Rectangle
                            {
                                id: showCameraIcon
                                width: 30 * screenScaleFactor
                                height: width
                                radius: width
                                anchors.left: parent.left
                                anchors.rightMargin: UM.Theme.getSize("default_margin").width
                                anchors.bottom: printJobPreview.bottom
                                color: UM.Theme.getColor("setting_control_border_highlight")
                                Image
                                {
                                    width: parent.width
                                    height: width
                                    anchors.right: parent.right
                                    anchors.rightMargin: parent.rightMargin
                                    source: "camera-icon.svg"
                                }
                            }
                        }
                    }

                    ProgressBar
                    {
                        property var progress:
                        {
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

                                if(modelData.activePrintJob.state == "wait_cleanup")
                                {
                                    return "Finshed"
                                }
                                else if(modelData.activePrintJob.state == "pre_print")
                                {
                                    return "Preparing"
                                }
                                else
                                {
                                    return OutputDevice.formatDuration(modelData.activePrintJob.timeTotal - modelData.activePrintJob.timeElapsed)
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
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
