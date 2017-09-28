// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura
import "Menus"

Rectangle
{
    id: base
    anchors.left: parent.left
    anchors.right: parent.right
    height: UM.Theme.getSize("sidebar_header").height
    color: base.monitoringPrint ? UM.Theme.getColor("topbar_background_color_monitoring") : UM.Theme.getColor("topbar_background_color")

    Behavior on color { ColorAnimation { duration: 100; } }

    property bool printerConnected: Cura.MachineManager.printerOutputDevices.length != 0
    property bool printerAcceptsCommands: printerConnected && Cura.MachineManager.printerOutputDevices[0].acceptsCommands
    property bool monitoringPrint: false

    // outgoing signal
    signal startMonitoringPrint()
    signal stopMonitoringPrint()

    // update monitoring status when event was triggered outside topbar
    Component.onCompleted: {
        startMonitoringPrint.connect(function () {
            base.monitoringPrint = true
        })
        stopMonitoringPrint.connect(function () {
            base.monitoringPrint = false
        })
    }

    UM.I18nCatalog
    {
        id: catalog
        name:"cura"
    }

    Image
    {
        id: logo
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        anchors.verticalCenter: parent.verticalCenter

        source: UM.Theme.getImage("logo");
        width: UM.Theme.getSize("logo").width;
        height: UM.Theme.getSize("logo").height;

        sourceSize.width: width;
        sourceSize.height: height;
    }

    Row
    {
        anchors.left: logo.right
        anchors.leftMargin: UM.Theme.getSize("topbar_logo_right_margin").width
        anchors.right: machineSelection.left
        anchors.rightMargin: UM.Theme.getSize("default_margin").width
        spacing: UM.Theme.getSize("default_margin").width

        Button
        {
            id: showSettings
            height: UM.Theme.getSize("sidebar_header").height
            text: catalog.i18nc("@title:tab", "Prepare")
            checkable: true
            checked: isChecked()
            exclusiveGroup: sidebarHeaderBarGroup
            style: UM.Theme.styles.topbar_header_tab

            // We use a Qt.binding to re-bind the checkbox state after manually setting it
            // https://stackoverflow.com/questions/38798450/qt-5-7-qml-why-are-my-checkbox-property-bindings-disappearing
            onClicked: {
                base.stopMonitoringPrint()
                checked = Qt.binding(isChecked)
            }

            function isChecked () {
                return !base.monitoringPrint
            }

            property color overlayColor: "transparent"
            property string overlayIconSource: ""
        }

        Button
        {
            id: showMonitor
            width: UM.Theme.getSize("topbar_button").width
            height: UM.Theme.getSize("sidebar_header").height
            text: catalog.i18nc("@title:tab", "Monitor")
            checkable: true
            checked: isChecked()
            exclusiveGroup: sidebarHeaderBarGroup
            style: UM.Theme.styles.topbar_header_tab_no_overlay

            // We use a Qt.binding to re-bind the checkbox state after manually setting it
            // https://stackoverflow.com/questions/38798450/qt-5-7-qml-why-are-my-checkbox-property-bindings-disappearing
            onClicked: {
                base.startMonitoringPrint()
                checked = Qt.binding(isChecked)
            }

            function isChecked () {
                return base.monitoringPrint
            }

            property string iconSource:
            {
                if (!printerConnected)
                {
                    return UM.Theme.getIcon("tab_status_unknown");
                }
                else if (!printerAcceptsCommands)
                {
                    return UM.Theme.getIcon("tab_status_unknown");
                }

                if (Cura.MachineManager.printerOutputDevices[0].printerState == "maintenance")
                {
                    return UM.Theme.getIcon("tab_status_busy");
                }

                switch (Cura.MachineManager.printerOutputDevices[0].jobState)
                {
                    case "printing":
                    case "pre_print":
                    case "pausing":
                    case "resuming":
                        return UM.Theme.getIcon("tab_status_busy");
                    case "wait_cleanup":
                        return UM.Theme.getIcon("tab_status_finished");
                    case "ready":
                    case "":
                        return UM.Theme.getIcon("tab_status_connected")
                    case "paused":
                        return UM.Theme.getIcon("tab_status_paused")
                    case "error":
                        return UM.Theme.getIcon("tab_status_stopped")
                    default:
                        return UM.Theme.getIcon("tab_status_unknown")
                }
            }
        }

        ExclusiveGroup { id: sidebarHeaderBarGroup }
    }

    ToolButton
    {
        id: machineSelection
        text: Cura.MachineManager.activeMachineName

        width: UM.Theme.getSize("sidebar").width
        height: UM.Theme.getSize("sidebar_header").height
        tooltip: Cura.MachineManager.activeMachineName

        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        style: ButtonStyle
        {
            background: Rectangle
            {
                color:
                {
                    if(control.pressed)
                    {
                        return UM.Theme.getColor("sidebar_header_active");
                    }
                    else if(control.hovered)
                    {
                        return UM.Theme.getColor("sidebar_header_hover");
                    }
                    else
                    {
                        return UM.Theme.getColor("sidebar_header_bar");
                    }
                }
                Behavior on color { ColorAnimation { duration: 50; } }

                UM.RecolorImage
                {
                    id: downArrow
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    anchors.rightMargin: UM.Theme.getSize("default_margin").width
                    width: UM.Theme.getSize("standard_arrow").width
                    height: UM.Theme.getSize("standard_arrow").height
                    sourceSize.width: width
                    sourceSize.height: width
                    color: UM.Theme.getColor("text_emphasis")
                    source: UM.Theme.getIcon("arrow_bottom")
                }
                Label
                {
                    id: sidebarComboBoxLabel
                    color: UM.Theme.getColor("sidebar_header_text_active")
                    text: control.text;
                    elide: Text.ElideRight;
                    anchors.left: parent.left;
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width * 2
                    anchors.right: downArrow.left;
                    anchors.rightMargin: control.rightMargin;
                    anchors.verticalCenter: parent.verticalCenter;
                    font: UM.Theme.getFont("large")
                }
            }
            label: Label {}
        }

        menu: PrinterMenu { }
    }

    ComboBox
    {
        id: viewModeButton
        anchors
        {
            verticalCenter: parent.verticalCenter
            right: parent.right
            rightMargin: UM.Theme.getSize("sidebar").width + UM.Theme.getSize("default_margin").width
        }
        style: UM.Theme.styles.combobox
        visible: !base.monitoringPrint

        model: UM.ViewModel { }
        textRole: "name"

        onCurrentIndexChanged:
        {
            UM.Controller.setActiveView(model.getItem(currentIndex).id);

            // Update the active flag
            for (var i = 0; i < model.rowCount; ++i)
            {
                const is_active = i == currentIndex;
                model.getItem(i).active = is_active;
            }
        }

        currentIndex:
        {
            for (var i = 0; i < model.rowCount; ++i)
            {
                if (model.getItem(i).active)
                {
                    return i;
                }
            }
            return 0;
        }
    }

    Loader
    {
        id: view_panel

        anchors.top: viewModeButton.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.right: viewModeButton.right

        property var buttonTarget: Qt.point(viewModeButton.x + viewModeButton.width / 2, viewModeButton.y + viewModeButton.height / 2)

        height: childrenRect.height;

        source: UM.ActiveView.valid ? UM.ActiveView.activeViewPanel : "";
    }

}
