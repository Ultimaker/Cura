// Copyright (c) 2026 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import UM 1.7 as UM
import Cura 1.0 as Cura

Item
{
    id: base

    // NOTE: Uses the main child's dimensions directly, since childrenRect is only updated on _growing_, not _shrinking_.
    width: mainColumn.width
    height: mainColumn.height
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

    property UM.SettingPropertyProvider supportEnabled: UM.SettingPropertyProvider
    {
        id: supportEnabled
        containerStack: Cura.MachineManager.activeMachine
        key: "support_enable"
        watchedProperties: [ "value" ]
        storeIndex: 0
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
                text: catalog.i18nc("@action:button", "Material")
                icon: "Extruder"
                tooltipText: catalog.i18nc("@tooltip", "Paint on model to select the material to be used")
                mode: "extruder"
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
            visible: !rowExtruder.visible

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
            id: rowExtruder
            visible: UM.Controller.properties.getValue("PaintType") === "extruder"

            UM.Label
            {
                text: catalog.i18nc("@label", "Mark as")
            }

            Repeater
            {
                id: repeaterExtruders
                model: CuraApplication.getExtrudersModel()
                delegate: Cura.ExtruderButton
                {
                    extruder: model

                    checked: UM.Controller.properties.getValue("BrushExtruder") === model.index
                    onClicked: UM.Controller.setProperty("BrushExtruder", model.index)
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
            to: 100
            value: UM.Controller.properties.getValue("BrushSize")

            onPressedChanged: function(pressed)
            {
                if(! pressed)
                {
                    UM.Controller.setProperty("BrushSize", shapeSizeSlider.value);
                }
            }
        }

        UM.Label
        {
            id: supportAngleLabel
            text: catalog.i18nc("@label", "Auto-Support Overhang")
            visible: UM.Controller.properties.getValue("PaintType") === "support" && supportEnabled.properties.value == "True"
        }

        Cura.TertiaryButton
        {
            text: catalog.i18nc("@label", "<b>Enable auto-support</b>")
            visible: UM.Controller.properties.getValue("PaintType") === "support" && supportEnabled.properties.value == "False"
            onClicked: supportEnabled.setPropertyValue("value", true)
            height: supportAngleLabel.height + supportAngleSlider.height + UM.Theme.getSize("default_margin").height
        }

        RowLayout
        {
            id: supportAngleSlider
            width: parent.width
            visible: UM.Controller.properties.getValue("PaintType") === "support" && supportEnabled.properties.value == "True"
            height: childrenRect.height

            Cura.SingleSettingSlider
            {
                Layout.minimumHeight: parent.visible ? UM.Theme.getSize("combobox").height : 0.0
                Layout.fillHeight: true
                Layout.minimumWidth: parent.width / 2.0
                Layout.fillWidth: true

                from: 0
                to: 90
                stepSize: 5
                tooltipUnit: "°"
                settingName: "support_angle"
                updateAllExtruders: true
            }

            Cura.SingleSettingTextField
            {
                Layout.minimumHeight: parent.visible ? UM.Theme.getSize("combobox").height : 0.0
                Layout.fillHeight: true
                Layout.minimumWidth: UM.Theme.getSize("large_button").width
                Layout.fillWidth: false

                settingName: "support_angle"
                updateAllExtruders: true
                validator: UM.FloatValidator {}
                unitText: "°"
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
                text: catalog.i18nc("@action:button", "Undo Stroke (Ctrl+L)")
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
                text: catalog.i18nc("@action:button", "Redo Stroke (Ctrl+Shift+L)")
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
            text: catalog.i18nc("@label", "Select a single ungrouped model to start painting")
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
        }
    }

    Rectangle
    {
        id: warningLegacyOpenGLItem
        anchors.fill: parent
        color: UM.Theme.getColor("main_background")
        visible: UM.Controller.properties.getValue("State") === Cura.PaintToolState.NOT_SUPPORTED

        UM.Label
        {
            anchors.fill: parent
            text: catalog.i18nc("@label", "Painting is not available on this device. Your graphics card or drivers do not fully support it. Updating your graphics drivers may enable this feature.")
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
