import QtQuick 2.2
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Item {
    id: base

    width: buttons.width
    height: buttons.height
    property int activeY

    function showTooltip(item, position, text)
    {
        tooltip.text = text;
        position = item.mapToItem(base, position.x - UM.Theme.getSize("default_arrow").width, position.y);
        tooltip.show(position);
    }

    function hideTooltip()
    {
        tooltip.hide();
    }

    Item
    {
        id: buttons
        width: parent.visible ? columnButtons.width : 0
        height: childrenRect.height

        Behavior on width { NumberAnimation { duration: 100 } }


        // Used to create a rounded rectangle behind the extruderButtons
        // Rectangle {
        //     anchors {
        //         fill: extruderButtons
        //         leftMargin: -radius - border.width
        //         rightMargin: -border.width
        //         topMargin: -border.width
        //         bottomMargin: -border.width
        //     }
        //     radius: UM.Theme.getSize("default_radius").width
        //     color: UM.Theme.getColor("lining")
        //     visible: extrudersModel.items.length > 1
        // }

        Column
        {
            id: columnButtons

            anchors.topMargin: UM.Theme.getSize("default_margin").height
            //anchors.top: pausaButton.bottom
            anchors.right: parent.right
            spacing: UM.Theme.getSize("default_lining").height
            ToolbarButton {
                id: impresorasButton
                //text: catalog.i18nc("@button", "Manage printers")
                // anchors.topMargin: UM.Theme.getSize("default_margin").height
                // anchors.top: columnButtons.bottom
                // anchors.right: parent.right
                spacing: UM.Theme.getSize("default_lining").height
                enabled: true
                onClicked: {
                    machineSelection.visible = !machineSelection.visible;
                    if (machineSelection.visible) {
                        machineSelection.toggleContent(); 
                    }                             
                } 
                toolItem: UM.RecolorImage {
                    source: UM.Theme.getIcon("category_machine") 
                    color: UM.Theme.getColor("icon")
                    sourceSize: UM.Theme.getSize("button_icon")
                }
                //Seleccion de impresora
                Cura.MachineSelector {
                    id: machineSelection
                    visible: false
                    z: 1
                    anchors.left: parent.right
                    anchors.top: parent.top
                    height: 0
                    width: 0
                    collapseButtonVisible: false
                    // Layout.minimumWidth: UM.Theme.getSize("machine_selector_widget").width
                    Layout.maximumWidth: 0
                    // Layout.fillWidth: true
                }                

            }
            ToolbarButton {
                id: settingsButton
                //text: catalog.i18nc("@label", "Print settings")
                // anchors.topMargin: UM.Theme.getSize("default_margin").height
                // anchors.top: columnButtons.bottom
                // anchors.right: parent.right
                spacing: UM.Theme.getSize("default_lining").height
                enabled: true
                onClicked: {
                    printSetup.visible = !printSetup.visible;
                    if (!printSetup.expanded) {
                        printSetup.toggleContent(); 
                    }                                   
                } 
                toolItem: UM.RecolorImage {
                    source: UM.Theme.getIcon("settings") 
                    color: UM.Theme.getColor("icon")
                    sourceSize: UM.Theme.getSize("button_icon")
                }
                //Menú de parámetros de impresión
                Cura.PrintSetupSelector {
                    id: printSetup
                    visible: false
                    z: 0
                    anchors.left: parent.right
                    
                    width: UM.Theme.getSize("print_setup_widget").width - 2 * UM.Theme.getSize("default_margin").width
                    implicitWidth: 400 * screenScaleFactor
                    height: parent.height
                    // height: 0
                    // width: 0
                    //collapseButtonVisible: false
                    // This is a work around to prevent the printSetupSelector from having to be re-loaded every time
                    // a stage switch is done.
                    // children: [printSetupSelector]
                    // height: childrenRect.height
                    // width: childrenRect.width
                }               

            }
            ToolbarButton {
                id: extrudersButton
                text: catalog.i18nc("@label", "Configuration Panel")

                spacing: UM.Theme.getSize("default_lining").height
                enabled: true
                onClicked: {
                    configurationMenu.visible = !configurationMenu.visible;   
                    if (configurationMenu.visible) {
                        configurationMenu.toggleContent(); 
                    }                                 
                } 
                toolItem: UM.RecolorImage {
                    source: UM.Theme.getIcon("extruder_button") 
                    color: UM.Theme.getColor("icon")
                    sourceSize: UM.Theme.getSize("button_icon")
                }
                       //Menú extruders
                Cura.ConfigurationMenu {
                    visible: false
                    id: configurationMenu
                    z: 0
                    anchors.left: parent.right
                    width: UM.Theme.getSize("configuration_selector").width
                    height: parent.height
                } 
            }
        } 
    }


    UM.PointingRectangle {
        id: panelBorder

        anchors.right: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        anchors.top: base.top
        //anchors.topMargin: base.activeY
        z: buttons.z - 1

        target: Qt.point(parent.right, base.activeY +  Math.round(UM.Theme.getSize("button").height/2))
        arrowSize: UM.Theme.getSize("default_arrow").width

        width: {
            if (panel.item && panel.width > 0) {
                 return Math.max(panel.width + 2 * UM.Theme.getSize("default_margin").width)
            }
            else {
                return 0;
            }
        }
        height: panel.item ? panel.height + 2 * UM.Theme.getSize("default_margin").height : 0

        opacity: panel.item && panel.width > 0 ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 100 } }

        color: UM.Theme.getColor("tool_panel_background")
        borderColor: UM.Theme.getColor("lining")
        borderWidth: UM.Theme.getSize("default_lining").width

        MouseArea //Catch all mouse events (so scene doesnt handle them)
        {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
            onWheel: wheel.accepted = true
        }

        Loader {
            id: panel

            x: UM.Theme.getSize("default_margin").width
            y: UM.Theme.getSize("default_margin").height

            source: UM.ActiveTool.valid ? UM.ActiveTool.activeToolPanel : ""
            enabled: UM.Controller.toolsEnabled
        }
    }

    // This rectangle displays the information about the current angle etc. when
    // dragging a tool handle.
    Rectangle {
        id: toolInfo
        x: visible ? -base.x + base.mouseX + UM.Theme.getSize("default_margin").width: 0
        y: visible ? -base.y + base.mouseY + UM.Theme.getSize("default_margin").height: 0

        width: toolHint.width + UM.Theme.getSize("default_margin").width
        height: toolHint.height;
        color: UM.Theme.getColor("tooltip")
        Label
        {
            id: toolHint
            text: UM.ActiveTool.properties.getValue("ToolHint") != undefined ? UM.ActiveTool.properties.getValue("ToolHint") : ""
            color: UM.Theme.getColor("tooltip_text")
            font: UM.Theme.getFont("default")
            anchors.horizontalCenter: parent.horizontalCenter
        }

        visible: toolHint.text != ""
    }

    states: [
        State {
            name: "anchorAtTop"

            AnchorChanges {
                target: panelBorder
                anchors.top: base.top
                anchors.bottom: undefined
            }
            PropertyChanges {
                target: panelBorder
                anchors.topMargin: base.activeY
            }
        },
        State {
            name: "anchorAtBottom"

            AnchorChanges {
                target: panelBorder
                anchors.top: undefined
                anchors.bottom: base.top
            }
            PropertyChanges {
                target: panelBorder
                anchors.bottomMargin: {
                    if (panelBorder.height > (base.activeY + UM.Theme.getSize("button").height)) {
                        // panel is tall, align the top of the panel with the top of the first tool button
                        return -panelBorder.height
                    }
                    // align the bottom of the panel with the bottom of the selected tool button
                    return -(base.activeY + UM.Theme.getSize("button").height)
                }
            }
        }
    ]
}
