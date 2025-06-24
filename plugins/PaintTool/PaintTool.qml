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
        onTriggered: UM.Controller.triggerActionWithData("undoStackAction", false)
    }

    Action
    {
        id: redoAction
        shortcut: "Ctrl+Shift+L"
        onTriggered: UM.Controller.triggerActionWithData("undoStackAction", true)
    }

    ColumnLayout
    {
        RowLayout
        {
            UM.ToolbarButton
            {
                id: paintTypeA

                text: catalog.i18nc("@action:button", "Paint Type A")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("Buildplate")
                    color: UM.Theme.getColor("icon")
                }
                property bool needBorder: true

                z: 2

                onClicked: UM.Controller.triggerActionWithData("setPaintType", "A")
            }

            UM.ToolbarButton
            {
                id: paintTypeB

                text: catalog.i18nc("@action:button", "Paint Type B")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("BlackMagic")
                    color: UM.Theme.getColor("icon")
                }
                property bool needBorder: true

                z: 2

                onClicked: UM.Controller.triggerActionWithData("setPaintType", "B")
            }
        }

        RowLayout
        {
            UM.ToolbarButton
            {
                id: colorButtonA

                text: catalog.i18nc("@action:button", "Color A")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("Eye")
                    color: "purple"
                }
                property bool needBorder: true

                z: 2

                onClicked: UM.Controller.triggerActionWithData("setBrushColor", "A")
            }

            UM.ToolbarButton
            {
                id: colorButtonB

                text: catalog.i18nc("@action:button", "Color B")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("Eye")
                    color: "orange"
                }
                property bool needBorder: true

                z: 2

                onClicked: UM.Controller.triggerActionWithData("setBrushColor", "B")
            }

            UM.ToolbarButton
            {
                id: colorButtonC

                text: catalog.i18nc("@action:button", "Color C")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("Eye")
                    color: "green"
                }
                property bool needBorder: true

                z: 2

                onClicked: UM.Controller.triggerActionWithData("setBrushColor", "C")
            }

            UM.ToolbarButton
            {
                id: colorButtonD

                text: catalog.i18nc("@action:button", "Color D")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("Eye")
                    color: "ghostwhite"
                }
                property bool needBorder: true

                z: 2

                onClicked: UM.Controller.triggerActionWithData("setBrushColor", "D")
            }
        }

        RowLayout
        {
            UM.ToolbarButton
            {
                id: shapeSquareButton

                text: catalog.i18nc("@action:button", "Square Brush")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("MeshTypeNormal")
                    color: UM.Theme.getColor("icon")
                }
                property bool needBorder: true

                z: 2

                onClicked: UM.Controller.triggerActionWithData("setBrushShape", Cura.PaintToolBrush.SQUARE)
            }

            UM.ToolbarButton
            {
                id: shapeCircleButton

                text: catalog.i18nc("@action:button", "Round Brush")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("CircleOutline")
                    color: UM.Theme.getColor("icon")
                }
                property bool needBorder: true

                z: 2

                onClicked: UM.Controller.triggerActionWithData("setBrushShape", Cura.PaintToolBrush.CIRCLE)
            }

            UM.Slider
            {
                id: shapeSizeSlider

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
                }
                property bool needBorder: true

                z: 2

                onClicked: undoAction.trigger()
            }

            UM.ToolbarButton
            {
                id: redoButton

                text: catalog.i18nc("@action:button", "Redo Stroke")
                toolItem: UM.ColorImage
                {
                    source: UM.Theme.getIcon("ArrowDoubleCircleRight")
                }
                property bool needBorder: true

                z: 2

                onClicked: redoAction.trigger()
            }
        }
    }
}
