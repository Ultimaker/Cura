// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.3

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: base

    width: buttons.width
    height: buttons.height
    property int activeY

    Item
    {
        id: buttons
        width: parent.visible ? toolButtons.width : 0
        height: childrenRect.height

        Behavior on width { NumberAnimation { duration: 100 } }

        // Used to create a rounded rectangle behind the toolButtons
        Rectangle
        {
            anchors
            {
                fill: toolButtons
                leftMargin: -radius - border.width
                rightMargin: -border.width
                topMargin: -border.width
                bottomMargin: -border.width
            }
            radius: UM.Theme.getSize("default_radius").width
            color: UM.Theme.getColor("lining")
        }

        Column
        {
            id: toolButtons

            anchors.top: parent.top
            anchors.right: parent.right

            Repeater
            {
                id: repeat

                model: UM.ToolModel { id: toolsModel }
                width: childrenRect.width
                height: childrenRect.height

                delegate: ToolbarButton
                {
                    text: model.name + (model.shortcut ? (" (" + model.shortcut + ")") : "")
                    checkable: true
                    checked: model.active
                    enabled: model.enabled && UM.Selection.hasSelection && UM.Controller.toolsEnabled

                    isTopElement: toolsModel.getItem(0).id == model.id
                    isBottomElement: toolsModel.getItem(toolsModel.count - 1).id == model.id

                    toolItem: UM.RecolorImage
                    {
                        source: UM.Theme.getIcon(model.icon) != "" ? UM.Theme.getIcon(model.icon) : "file:///" + model.location + "/" + model.icon
                        color: UM.Theme.getColor("icon")

                        sourceSize.height: Math.round(UM.Theme.getSize("button").height / 2)
                        sourceSize.width: Math.round(UM.Theme.getSize("button").width / 2)
                    }

                    onCheckedChanged:
                    {
                        if (checked)
                        {
                            base.activeY = y;
                        }
                        //Clear focus when tools change. This prevents the tool grabbing focus when activated.
                        //Grabbing focus prevents items from being deleted.
                        //Apparently this was only a problem on MacOS.
                        forceActiveFocus();
                    }

                    //Workaround since using ToolButton's onClicked would break the binding of the checked property, instead
                    //just catch the click so we do not trigger that behaviour.
                    MouseArea
                    {
                        anchors.fill: parent;
                        onClicked:
                        {
                            forceActiveFocus() //First grab focus, so all the text fields are updated
                            if(parent.checked)
                            {
                                UM.Controller.setActiveTool(null);
                            }
                            else
                            {
                                UM.Controller.setActiveTool(model.id);
                            }

                            base.state = (index < toolsModel.count/2) ? "anchorAtTop" : "anchorAtBottom";
                        }
                    }
                }
            }
        }

        // Used to create a rounded rectangle behind the extruderButtons
        Rectangle
        {
            anchors
            {
                fill: extruderButtons
                leftMargin: -radius - border.width
                rightMargin: -border.width
                topMargin: -border.width
                bottomMargin: -border.width
            }
            radius: UM.Theme.getSize("default_radius").width
            color: UM.Theme.getColor("lining")
            visible: extrudersModel.items.length > 1
        }

        Column
        {
            id: extruderButtons

            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.top: toolButtons.bottom
            anchors.right: parent.right

            Repeater
            {
                width: childrenRect.width
                height: childrenRect.height
                model: extrudersModel.items.length > 1 ? extrudersModel : 0

                delegate: ExtruderButton
                {
                    extruder: model
                    isTopElement: extrudersModel.getItem(0).id == model.id
                    isBottomElement: extrudersModel.getItem(extrudersModel.rowCount() - 1).id == model.id
                }
            }
        }
    }

    property var extrudersModel: CuraApplication.getExtrudersModel()

    UM.PointingRectangle
    {
        id: panelBorder

        anchors.left: parent.right
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        anchors.top: base.top
        anchors.topMargin: base.activeY
        z: buttons.z - 1

        target: Qt.point(parent.right, base.activeY +  Math.round(UM.Theme.getSize("button").height/2))
        arrowSize: UM.Theme.getSize("default_arrow").width

        width:
        {
            if (panel.item && panel.width > 0)
            {
                 return Math.max(panel.width + 2 * UM.Theme.getSize("default_margin").width)
            }
            else
            {
                return 0;
            }
        }
        height: panel.item ? panel.height + 2 * UM.Theme.getSize("default_margin").height : 0

        opacity: panel.item && panel.width > 0 ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 100 } }

        color: UM.Theme.getColor("tool_panel_background")
        borderColor: UM.Theme.getColor("lining")
        borderWidth: UM.Theme.getSize("default_lining").width

        MouseArea //Catch all mouse events (so scene doesn't handle them)
        {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
            onWheel: wheel.accepted = true
        }

        Loader
        {
            id: panel

            x: UM.Theme.getSize("default_margin").width
            y: UM.Theme.getSize("default_margin").height

            source: UM.ActiveTool.valid ? UM.ActiveTool.activeToolPanel : ""
            enabled: UM.Controller.toolsEnabled
        }
    }

    // This rectangle displays the information about the current angle etc. when
    // dragging a tool handle.
    Rectangle
    {
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
