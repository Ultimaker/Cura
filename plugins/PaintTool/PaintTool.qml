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

    Action
    {
        id: undoAction
        shortcut: "Ctrl+L"
        enabled: UM.Controller.properties.getValue("CanUndo")
        onTriggered: UM.Controller.triggerAction("undoStackAction")
    }

    Action
    {
        id: redoAction
        shortcut: "Ctrl+Shift+L"
        enabled: UM.Controller.properties.getValue("CanRedo")
        onTriggered: UM.Controller.triggerAction("redoStackAction")
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
                visible: false
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

            from: 10
            to: 1000
            value: UM.Controller.properties.getValue("BrushSize")

            onPressedChanged: function(pressed)
            {
                if(! pressed)
                {
                    UM.Controller.setProperty("BrushSize", shapeSizeSlider.value);
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

                enabled: undoAction.enabled
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

                enabled: redoAction.enabled
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

    Rectangle
    {
        id: waitPrepareItem
        anchors.fill: parent
        color: UM.Theme.getColor("main_background")
        visible: UM.Controller.properties.getValue("State") === Cura.PaintToolState.PREPARING_MODEL

        ColumnLayout
        {
            anchors.fill: parent

            UM.Label
            {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.verticalStretchFactor: 2

                text: catalog.i18nc("@label", "Preparing model for painting...")
                verticalAlignment: Text.AlignBottom
                horizontalAlignment: Text.AlignHCenter
            }

            Item
            {
                Layout.preferredWidth: loadingIndicator.width
                Layout.alignment: Qt.AlignHCenter
                Layout.fillHeight: true
                Layout.verticalStretchFactor: 1

                UM.ColorImage
                {
                    id: loadingIndicator

                    anchors.top: parent.top
                    anchors.left: parent.left
                    width: UM.Theme.getSize("card_icon").width
                    height: UM.Theme.getSize("card_icon").height
                    source: UM.Theme.getIcon("ArrowDoubleCircleRight")
                    color: UM.Theme.getColor("text_default")

                    RotationAnimator
                    {
                        target: loadingIndicator
                        from: 0
                        to: 360
                        duration: 2000
                        loops: Animation.Infinite
                        running: true
                        alwaysRunToEnd: true
                    }
                }
            }
        }
    }

    Rectangle
    {
        id: selectSingleMessageItem
        anchors.fill: parent
        color: UM.Theme.getColor("main_background")
        visible: UM.Controller.properties.getValue("State") === Cura.PaintToolState.MULTIPLE_SELECTION

        UM.Label
        {
            anchors.fill: parent
            text: catalog.i18nc("@label", "Select a single model to start painting")
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
