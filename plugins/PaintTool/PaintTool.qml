// Copyright (c) 2025 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import UM 1.7 as UM
import Cura 1.0 as Cura

Item
{
    id: base
    width: childrenRect.width
    height: childrenRect.height
    UM.I18nCatalog { id: catalog; name: "cura"}

    property string selectedMode: ""
    property string selectedColor: ""
    property int selectedShape: 0

    Action
    {
        id: undoAction
        shortcut: "Ctrl+L"
        onTriggered: UM.Controller.triggerActionWithData("undoStackAction", false)
    }

    Action
    {
        id: redoAction
        shortcut: "Ctrl+Shift+L"
        onTriggered: UM.Controller.triggerActionWithData("undoStackAction", true)
    }

    Column
    {
        id: mainColumn
        spacing: UM.Theme.getSize("default_margin").height

        RowLayout
        {
            id: rowPaintMode
            width: parent.width

            PaintModeButton
            {
                text: catalog.i18nc("@action:button", "Seam")
                icon: "Seam"
                tooltipText: catalog.i18nc("@tooltip", "Refine seam placement by defining preferred/avoidance areas")
                mode: "seam"
            }

            PaintModeButton
            {
                text: catalog.i18nc("@action:button", "Support")
                icon: "Support"
                tooltipText: catalog.i18nc("@tooltip", "Refine support placement by defining preferred/avoidance areas")
                mode: "support"
            }
        }

        //Line between the sections.
        Rectangle
        {
            width: parent.width
            height: UM.Theme.getSize("default_lining").height
            color: UM.Theme.getColor("lining")
        }

        RowLayout
        {
            id: rowBrushColor

            UM.Label
            {
                text: catalog.i18nc("@label", "Mark as")
            }

            BrushColorButton
            {
                id: buttonPreferredArea
                color: "preferred"

                text: catalog.i18nc("@action:button", "Preferred")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("CheckBadge", "low")
                    color: UM.Theme.getColor("paint_preferred_area")
                }
            }

            BrushColorButton
            {
                id: buttonAvoidArea
                color: "avoid"

                text: catalog.i18nc("@action:button", "Avoid")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("CancelBadge", "low")
                    color: UM.Theme.getColor("paint_avoid_area")
                }
            }

            BrushColorButton
            {
                id: buttonEraseArea
                color: "none"

                text: catalog.i18nc("@action:button", "Erase")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("Eraser")
                    color: UM.Theme.getColor("icon")
                }
            }
        }

        RowLayout
        {
            id: rowBrushShape

            UM.Label
            {
                text: catalog.i18nc("@label", "Brush Shape")
            }

            BrushShapeButton
            {
                id: buttonBrushCircle
                shape: Cura.PaintToolBrush.CIRCLE

                text: catalog.i18nc("@action:button", "Circle")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("Circle")
                    color: UM.Theme.getColor("icon")
                }
            }

            BrushShapeButton
            {
                id: buttonBrushSquare
                shape: Cura.PaintToolBrush.SQUARE

                text: catalog.i18nc("@action:button", "Square")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("MeshTypeNormal")
                    color: UM.Theme.getColor("icon")
                }
            }
        }

        UM.Label
        {
            text: catalog.i18nc("@label", "Brush Size")
        }

        UM.Slider
        {
            id: shapeSizeSlider
            width: parent.width
            indicatorVisible: false

            from: 1
            to: 40
            value: 10

            onPressedChanged: function(pressed)
            {
                if(! pressed)
                {
                    UM.Controller.triggerActionWithData("setBrushSize", shapeSizeSlider.value)
                }
            }
        }

        //Line between the sections.
        Rectangle
        {
            width: parent.width
            height: UM.Theme.getSize("default_lining").height
            color: UM.Theme.getColor("lining")
        }

        RowLayout
        {
            UM.ToolbarButton
            {
                id: undoButton

                text: catalog.i18nc("@action:button", "Undo Stroke")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("ArrowReset")
                    color: UM.Theme.getColor("icon")
                }

                onClicked: undoAction.trigger()
            }

            UM.ToolbarButton
            {
                id: redoButton

                text: catalog.i18nc("@action:button", "Redo Stroke")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("ArrowReset")
                    color: UM.Theme.getColor("icon")
                    transform: [
                        Scale { xScale: -1; origin.x: width/2 }
                    ]
                }

                onClicked: redoAction.trigger()
            }

            Cura.SecondaryButton
            {
                id: clearButton
                text: catalog.i18nc("@button", "Clear all")
                onClicked: UM.Controller.triggerAction("clear")
            }
        }
    }

    Component.onCompleted:
    {
        // Force first types for consistency, otherwise UI may become different from controller
        rowPaintMode.children[0].setMode()
        rowBrushColor.children[1].setColor()
        rowBrushShape.children[1].setShape()
    }
}
