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
    property bool is_simulation_playing: false
    visible: UM.SimulationView.layerActivity && CuraApplication.platformActivity

    PathSlider
    {
        id: pathSlider
        height: UM.Theme.getSize("slider_handle").width
        width: UM.Theme.getSize("slider_layerview_size").height

        anchors.bottom: parent.bottom
        anchors.bottomMargin: UM.Theme.getSize("default_margin").height

        anchors.horizontalCenter: parent.horizontalCenter

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
        iconSource: !is_simulation_playing ? "./resources/simulation_resume.svg": "./resources/simulation_pause.svg"
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
            if(is_simulation_playing)
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
            is_simulation_playing = false
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
            if (!is_simulation_playing)
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
            is_simulation_playing = true
        }
    }

    LayerSlider
    {
        id: layerSlider

        width: UM.Theme.getSize("slider_handle").width
        height: UM.Theme.getSize("slider_layerview_size").height

        anchors
        {
            right: parent.right
            verticalCenter: parent.verticalCenter
            rightMargin: UM.Theme.getSize("default_margin").width
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