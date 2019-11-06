// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.4
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.4 as UM
import Cura 1.0 as Cura

Item
{
    // An Item whose bounds are guaranteed to be safe for overlays to be placed.
    // Defaults to parent, ie. the entire available area
    // eg. the layer slider will not be placed in this area.
    property var safeArea: parent


    property bool isSimulationPlaying: false
    readonly property real layerSliderSafeYMin: safeArea.y
    readonly property real layerSliderSafeYMax: safeArea.y + safeArea.height
    readonly property real pathSliderSafeXMin: safeArea.x + playButton.width
    readonly property real pathSliderSafeXMax: safeArea.x + safeArea.width

    visible: UM.SimulationView.layerActivity && CuraApplication.platformActivity

    // A slider which lets users trace a single layer (XY movements)
    PathSlider
    {
        id: pathSlider

        readonly property real preferredWidth: UM.Theme.getSize("slider_layerview_size").height // not a typo, should be as long as layerview slider
        readonly property real margin: UM.Theme.getSize("default_margin").width
        readonly property real pathSliderSafeWidth: pathSliderSafeXMax - pathSliderSafeXMin

        height: UM.Theme.getSize("slider_handle").width
        width: preferredWidth + margin * 2 < pathSliderSafeWidth ? preferredWidth : pathSliderSafeWidth - margin * 2


        anchors.bottom: parent.bottom
        anchors.bottomMargin: margin

        anchors.horizontalCenter: parent.horizontalCenter
        anchors.horizontalCenterOffset: -(parent.width - pathSliderSafeXMax - pathSliderSafeXMin) / 2 // center between parent top and layerSliderSafeYMax


        visible: !UM.SimulationView.compatibilityMode

        // Custom properties
        handleValue: UM.SimulationView.currentPath
        maximumValue: UM.SimulationView.numPaths

        // Update values when layer data changes.
        Connections
        {
            target: UM.SimulationView
            onMaxPathsChanged: pathSlider.setHandleValue(UM.SimulationView.currentPath)
            onCurrentPathChanged:
            {
                // Only pause the simulation when the layer was changed manually, not when the simulation is running
                if (pathSlider.manuallyChanged)
                {
                    playButton.pauseSimulation()
                }
                pathSlider.setHandleValue(UM.SimulationView.currentPath)
            }
        }

        // Ensure that the slider handlers show the correct value after switching views.
        Component.onCompleted:
        {
            pathSlider.setHandleValue(UM.SimulationView.currentPath)
        }

    }

    UM.SimpleButton
    {
        id: playButton
        iconSource: !isSimulationPlaying ? "./resources/simulation_resume.svg": "./resources/simulation_pause.svg"
        width: UM.Theme.getSize("small_button").width
        height: UM.Theme.getSize("small_button").height
        hoverColor: UM.Theme.getColor("slider_handle_active")
        color: UM.Theme.getColor("slider_handle")
        iconMargin: UM.Theme.getSize("thick_lining").width
        visible: !UM.SimulationView.compatibilityMode

        Connections
        {
            target: UM.Preferences
            onPreferenceChanged:
            {
                if (preference !== "view/only_show_top_layers" && preference !== "view/top_layer_count" && ! preference.match("layerview/"))
                {
                    return;
                }

                playButton.pauseSimulation()
            }
        }

        anchors
        {
            right: pathSlider.left
            verticalCenter: pathSlider.verticalCenter
        }

        onClicked:
        {
            if(isSimulationPlaying)
            {
                pauseSimulation()
            }
            else
            {
                resumeSimulation()
            }
        }

        function pauseSimulation()
        {
            UM.SimulationView.setSimulationRunning(false)
            simulationTimer.stop()
            isSimulationPlaying = false
            layerSlider.manuallyChanged = true
            pathSlider.manuallyChanged = true
        }

        function resumeSimulation()
        {
            UM.SimulationView.setSimulationRunning(true)
            simulationTimer.start()
            layerSlider.manuallyChanged = false
            pathSlider.manuallyChanged = false
        }
    }

    Timer
    {
        id: simulationTimer
        interval: 100
        running: false
        repeat: true
        onTriggered:
        {
            var currentPath = UM.SimulationView.currentPath
            var numPaths = UM.SimulationView.numPaths
            var currentLayer = UM.SimulationView.currentLayer
            var numLayers = UM.SimulationView.numLayers

            // When the user plays the simulation, if the path slider is at the end of this layer, we start
            // the simulation at the beginning of the current layer.
            if (!isSimulationPlaying)
            {
                if (currentPath >= numPaths)
                {
                    UM.SimulationView.setCurrentPath(0)
                }
                else
                {
                    UM.SimulationView.setCurrentPath(currentPath + 1)
                }
            }
            // If the simulation is already playing and we reach the end of a layer, then it automatically
            // starts at the beginning of the next layer.
            else
            {
                if (currentPath >= numPaths)
                {
                    // At the end of the model, the simulation stops
                    if (currentLayer >= numLayers)
                    {
                        playButton.pauseSimulation()
                    }
                    else
                    {
                        UM.SimulationView.setCurrentLayer(currentLayer + 1)
                        UM.SimulationView.setCurrentPath(0)
                    }
                }
                else
                {
                    UM.SimulationView.setCurrentPath(currentPath + 1)
                }
            }
            // The status must be set here instead of in the resumeSimulation function otherwise it won't work
            // correctly, because part of the logic is in this trigger function.
            isSimulationPlaying = true
        }
    }

    // Scrolls trough Z layers
    LayerSlider
    {
        property var preferredHeight: UM.Theme.getSize("slider_layerview_size").height
        property double heightMargin: UM.Theme.getSize("default_margin").height * 3 // extra margin to accomodate layer number tooltips
        property double layerSliderSafeHeight: layerSliderSafeYMax - layerSliderSafeYMin

        id: layerSlider

        width: UM.Theme.getSize("slider_handle").width
        height: preferredHeight + heightMargin * 2 < layerSliderSafeHeight ? preferredHeight : layerSliderSafeHeight - heightMargin * 2

        anchors
        {
            right: parent.right
            verticalCenter: parent.verticalCenter
            verticalCenterOffset: -(parent.height - layerSliderSafeYMax - layerSliderSafeYMin) / 2 // center between parent top and layerSliderSafeYMax
            rightMargin: UM.Theme.getSize("default_margin").width
            bottomMargin: heightMargin
            topMargin: heightMargin
        }

        // Custom properties
        upperValue: UM.SimulationView.currentLayer
        lowerValue: UM.SimulationView.minimumLayer
        maximumValue: UM.SimulationView.numLayers

        // Update values when layer data changes
        Connections
        {
            target: UM.SimulationView
            onMaxLayersChanged: layerSlider.setUpperValue(UM.SimulationView.currentLayer)
            onMinimumLayerChanged: layerSlider.setLowerValue(UM.SimulationView.minimumLayer)
            onCurrentLayerChanged:
            {
                // Only pause the simulation when the layer was changed manually, not when the simulation is running
                if (layerSlider.manuallyChanged)
                {
                    playButton.pauseSimulation()
                }
                layerSlider.setUpperValue(UM.SimulationView.currentLayer)
            }
        }

        // Make sure the slider handlers show the correct value after switching views
        Component.onCompleted:
        {
            layerSlider.setLowerValue(UM.SimulationView.minimumLayer)
            layerSlider.setUpperValue(UM.SimulationView.currentLayer)
        }
    }
}