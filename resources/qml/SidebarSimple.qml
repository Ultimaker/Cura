// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: base;

    signal showTooltip(Item item, point location, string text);
    signal hideTooltip();

    property Action configureSettings;
    property variant minimumPrintTime: PrintInformation.minimumPrintTime;
    property variant maximumPrintTime: PrintInformation.maximumPrintTime;
    property bool settingsEnabled: ExtruderManager.activeExtruderStackId || machineExtruderCount.properties.value == 1

    Component.onCompleted: PrintInformation.enabled = true
    Component.onDestruction: PrintInformation.enabled = false
    UM.I18nCatalog { id: catalog; name: "cura" }

    ScrollView
    {
        visible: Cura.MachineManager.activeMachineName != "" // If no printers added then the view is invisible
        anchors.fill: parent
        style: UM.Theme.styles.scrollview
        flickableItem.flickableDirection: Flickable.VerticalFlick

        Rectangle
        {
            width: childrenRect.width
            height: childrenRect.height
            color: UM.Theme.getColor("sidebar")

            //
            // Quality profile
            //
            Item
            {
                id: qualityRow

                height: UM.Theme.getSize("sidebar_margin").height
                anchors.topMargin: UM.Theme.getSize("sidebar_margin").height
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width
                anchors.right: parent.right

                Timer
                {
                    id: qualitySliderChangeTimer
                    interval: 50
                    running: false
                    repeat: false
                    onTriggered: Cura.MachineManager.setActiveQuality(Cura.ProfilesModel.getItem(qualitySlider.value).id)
                }

                Component.onCompleted: qualityModel.update()

                Connections
                {
                    target: Cura.MachineManager
                    onActiveQualityChanged: qualityModel.update()
                    onActiveMaterialChanged: qualityModel.update()
                }

                ListModel
                {
                    id: qualityModel

                    property var totalTicks: 0
                    property var availableTotalTicks: 0
                    property var activeQualityId: 0

                    property var qualitySliderStepWidth: 0
                    property var qualitySliderAvailableMin : 0
                    property var qualitySliderAvailableMax : 0
                    property var qualitySliderMarginRight : 0

                    function update () {
                        reset()

                        var availableMin = -1
                        var availableMax = -1

                        for (var i = 0; i <= Cura.ProfilesModel.rowCount(); i++) {
                            var qualityItem = Cura.ProfilesModel.getItem(i)

                            // Add each quality item to the UI quality model
                            qualityModel.append(qualityItem)

                            // Set selected value
                            if (Cura.MachineManager.activeQualityId == qualityItem.id) {
                                qualityModel.activeQualityId = i
                            }

                            // Set min available
                            if (qualityItem.available && availableMin == -1) {
                                availableMin = i
                            }

                            // Set max available
                            if (qualityItem.available) {
                                availableMax = i
                            }
                        }

                        // Set total available ticks for active slider part
                        if (availableMin != -1) {
                            qualityModel.availableTotalTicks = availableMax - availableMin
                        }

                        // Calculate slider values
                        calculateSliderStepWidth(qualityModel.totalTicks)
                        calculateSliderMargins(availableMin, availableMax, qualityModel.totalTicks)

                        qualityModel.qualitySliderAvailableMin = availableMin
                        qualityModel.qualitySliderAvailableMax = availableMax
                    }

                    function calculateSliderStepWidth (totalTicks) {
                        qualityModel.qualitySliderStepWidth = totalTicks != 0 ? (base.width * 0.55) / (totalTicks) : 0
                    }

                    function calculateSliderMargins (availableMin, availableMax, totalTicks) {
                        if (availableMin == -1 || (availableMin == 0 && availableMax == 0)) {
                            qualityModel.qualitySliderMarginRight = base.width * 0.55
                        } else if (availableMin == availableMax) {
                            qualityModel.qualitySliderMarginRight = (totalTicks - availableMin) * qualitySliderStepWidth
                        } else {
                            qualityModel.qualitySliderMarginRight = (totalTicks - availableMax) * qualitySliderStepWidth
                        }
                    }

                    function reset () {
                        qualityModel.clear()
                        qualityModel.availableTotalTicks = -1

                        // check, the ticks count cannot be less than zero
                        if(Cura.ProfilesModel.rowCount() != 0)
                            qualityModel.totalTicks = Cura.ProfilesModel.rowCount() - 1  // minus one, because slider starts from 0
                        else
                            qualityModel.totalTicks = 0
                    }
                }

                Text
                {
                    id: qualityRowTitle
                    text: catalog.i18nc("@label", "Layer Height")
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")
                }

                // Show titles for the each quality slider ticks
                Item
                {
                    y: -5;
                    anchors.left: speedSlider.left
                    Repeater
                    {
                        model: qualityModel

                        Text
                        {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.top: parent.top
                            anchors.topMargin: UM.Theme.getSize("sidebar_margin").height / 2
                            color: (Cura.MachineManager.activeMachine != null && Cura.ProfilesModel.getItem(index).available) ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                            text:
                            {
                                var result = ""
                                if(Cura.MachineManager.activeMachine != null){

                                    var result = Cura.ProfilesModel.getItem(index).layer_height_without_unit

                                    if(result == undefined)
                                        result = ""
                                }
                                return result
                            }

                            x: {
                                // Make sure the text aligns correctly with each tick
                                if (qualityModel.totalTicks == 0) {
                                    // If there is only one tick, align it centrally
                                    return ((base.width * 0.55) - width) / 2
                                } else if (index == 0) {
                                    return (base.width * 0.55 / qualityModel.totalTicks) * index
                                } else if (index == qualityModel.totalTicks) {
                                    return (base.width * 0.55 / qualityModel.totalTicks) * index - width
                                } else {
                                    return (base.width * 0.55 / qualityModel.totalTicks) * index - (width / 2)
                                }
                            }
                        }
                    }
                }

                //Print speed slider
                Item
                {
                    id: speedSlider
                    width: base.width * 0.55
                    height: UM.Theme.getSize("sidebar_margin").height
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.topMargin: UM.Theme.getSize("sidebar_margin").height

                    // Draw Unavailable line
                    Rectangle
                    {
                        id: groovechildrect
                        width: base.width * 0.55
                        height: 2 * screenScaleFactor
                        color: UM.Theme.getColor("quality_slider_unavailable")
                        anchors.verticalCenter: qualitySlider.verticalCenter
                        x: 0
                    }

                    // Draw ticks
                    Repeater
                    {
                        id: qualityRepeater
                        model: qualityModel.totalTicks > 0 ? qualityModel : 0

                        Rectangle
                        {
                            anchors.verticalCenter: parent.verticalCenter
                            color: Cura.ProfilesModel.getItem(index).available ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                            width: 1 * screenScaleFactor
                            height: 6 * screenScaleFactor
                            y: 0
                            x: qualityModel.qualitySliderStepWidth * index
                        }
                    }

                    Rectangle {
                        id: disabledHandleButton
                        visible: !qualitySlider.visible
                        anchors.centerIn: parent
                        color: UM.Theme.getColor("quality_slider_unavailable")
                        implicitWidth: 10 * screenScaleFactor
                        implicitHeight: implicitWidth
                        radius: width / 2
                    }

                    Slider
                    {
                        id: qualitySlider
                        height: UM.Theme.getSize("sidebar_margin").height
                        anchors.bottom: speedSlider.bottom
                        enabled: qualityModel.availableTotalTicks > 0
                        visible: qualityModel.totalTicks > 0
                        updateValueWhileDragging : false

                        minimumValue: qualityModel.qualitySliderAvailableMin >= 0 ? qualityModel.qualitySliderAvailableMin : 0
                        maximumValue: qualityModel.qualitySliderAvailableMax >= 0 ? qualityModel.qualitySliderAvailableMax : 0
                        stepSize: 1

                        value: qualityModel.activeQualityId

                        width: qualityModel.qualitySliderStepWidth * qualityModel.availableTotalTicks

                        anchors.right: parent.right
                        anchors.rightMargin: qualityModel.qualitySliderMarginRight

                        style: SliderStyle
                        {
                            //Draw Available line
                            groove: Rectangle {
                                implicitHeight: 2 * screenScaleFactor
                                color: UM.Theme.getColor("quality_slider_available")
                                radius: height / 2
                            }
                            handle: Item {
                                Rectangle {
                                    id: qualityhandleButton
                                    anchors.centerIn: parent
                                    color: UM.Theme.getColor("quality_slider_available")
                                    implicitWidth: 10 * screenScaleFactor
                                    implicitHeight: implicitWidth
                                    radius: implicitWidth / 2
                                }
                            }
                        }

                        onValueChanged: {
                            if(Cura.MachineManager.activeMachine != null)
                            {
                                //Prevent updating during view initializing. Trigger only if the value changed by user
                                if(qualitySlider.value != qualityModel.activeQualityId)
                                {
                                    //start updating with short delay
                                    qualitySliderChangeTimer.start();
                                }
                            }
                        }
                    }
                }

                Text
                {
                    id: speedLabel
                    anchors.top: speedSlider.bottom

                    anchors.left: parent.left

                    text: catalog.i18nc("@label", "Print Speed")
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")
                }

                Text
                {
                    anchors.bottom: speedLabel.bottom
                    anchors.left: speedSlider.left

                    text: catalog.i18nc("@label", "Slower")
                    font: UM.Theme.getFont("default")
                    color: (qualityModel.availableTotalTicks > 0) ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                    horizontalAlignment: Text.AlignLeft
                }

                Text
                {
                    anchors.bottom: speedLabel.bottom
                    anchors.right: speedSlider.right

                    text: catalog.i18nc("@label", "Faster")
                    font: UM.Theme.getFont("default")
                    color: (qualityModel.availableTotalTicks > 0) ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                    horizontalAlignment: Text.AlignRight
                }
            }



            //
            // Infill
            //
            Item
            {
                id: infillCellLeft

                anchors.top: qualityRow.bottom
                anchors.topMargin: UM.Theme.getSize("sidebar_margin").height * 2
                anchors.left: parent.left

                width: UM.Theme.getSize("sidebar").width * .45 - UM.Theme.getSize("sidebar_margin").width

                Text
                {
                    id: infillLabel
                    text: catalog.i18nc("@label", "Infill")
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")

                    anchors.top: parent.top
                    anchors.topMargin: UM.Theme.getSize("sidebar_margin").height * 1.7
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width
                }
            }

            Item
            {
                id: infillCellRight

                height: infillSlider.height + UM.Theme.getSize("sidebar_margin").height + enableGradualInfillCheckBox.visible * (enableGradualInfillCheckBox.height + UM.Theme.getSize("sidebar_margin").height)
                width: UM.Theme.getSize("sidebar").width * .55

                anchors.left: infillCellLeft.right
                anchors.top: infillCellLeft.top
                anchors.topMargin: UM.Theme.getSize("sidebar_margin").height

                Text {
                    id: selectedInfillRateText

                    //anchors.top: parent.top
                    anchors.left: infillSlider.left
                    anchors.leftMargin: (infillSlider.value / infillSlider.stepSize) * (infillSlider.width / (infillSlider.maximumValue / infillSlider.stepSize)) - 10 * screenScaleFactor
                    anchors.right: parent.right

                    text: infillSlider.value + "%"
                    horizontalAlignment: Text.AlignLeft

                    color: infillSlider.enabled ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                }

                Slider
                {
                    id: infillSlider

                    anchors.top: selectedInfillRateText.bottom
                    anchors.left: parent.left
                    anchors.right: infillIcon.left
                    anchors.rightMargin: UM.Theme.getSize("sidebar_margin").width

                    height: UM.Theme.getSize("sidebar_margin").height
                    width: infillCellRight.width - UM.Theme.getSize("sidebar_margin").width - style.handleWidth

                    minimumValue: 0
                    maximumValue: 100
                    stepSize: (parseInt(infillDensity.properties.value) % 10 == 0) ? 10 : 1
                    tickmarksEnabled: true

                    // disable slider when gradual support is enabled
                    enabled: parseInt(infillSteps.properties.value) == 0

                    // set initial value from stack
                    value: parseInt(infillDensity.properties.value)

                    onValueChanged: {
                        // Explicitly cast to string to make sure the value passed to Python is an integer.
                        infillDensity.setPropertyValue("value", String(parseInt(infillSlider.value)))
                    }

                    style: SliderStyle
                    {
                        groove: Rectangle {
                            id: groove
                            implicitWidth: 200 * screenScaleFactor
                            implicitHeight: 2 * screenScaleFactor
                            color: control.enabled ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                            radius: 1
                        }

                        handle: Item {
                            Rectangle {
                                id: handleButton
                                anchors.centerIn: parent
                                color: control.enabled ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                                implicitWidth: 10 * screenScaleFactor
                                implicitHeight: 10 * screenScaleFactor
                                radius: 10 * screenScaleFactor
                            }
                        }

                        tickmarks: Repeater {
                            id: repeater
                            model: control.maximumValue / control.stepSize + 1

                            // check if a tick should be shown based on it's index and wether the infill density is a multiple of 10 (slider step size)
                            function shouldShowTick (index) {
                                if ((parseInt(infillDensity.properties.value) % 10 == 0) || (index % 10 == 0)) {
                                    return true
                                }
                                return false
                            }

                            Rectangle {
                                anchors.verticalCenter: parent.verticalCenter
                                color: control.enabled ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                                width: 1 * screenScaleFactor
                                height: 6 * screenScaleFactor
                                y: 0
                                x: styleData.handleWidth / 2 + index * ((repeater.width - styleData.handleWidth) / (repeater.count-1))
                                visible: shouldShowTick(index)
                            }
                        }
                    }
                }

                Rectangle
                {
                    id: infillIcon

                    width: (parent.width / 5) - (UM.Theme.getSize("sidebar_margin").width)
                    height: width

                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.topMargin: UM.Theme.getSize("sidebar_margin").height / 2

                    // we loop over all density icons and only show the one that has the current density and steps
                    Repeater
                    {
                        id: infillIconList
                        model: infillModel
                        anchors.fill: parent

                        property int activeIndex: {
                            for (var i = 0; i < infillModel.count; i++) {
                                var density = parseInt(infillDensity.properties.value)
                                var steps = parseInt(infillSteps.properties.value)
                                var infillModelItem = infillModel.get(i)

                                if (density >= infillModelItem.percentageMin
                                    && density <= infillModelItem.percentageMax
                                    && steps >= infillModelItem.stepsMin
                                    && steps <= infillModelItem.stepsMax){
                                        return i
                                    }
                            }
                            return -1
                        }

                        Rectangle
                        {
                            anchors.fill: parent
                            visible: infillIconList.activeIndex == index

                            border.width: UM.Theme.getSize("default_lining").width
                            border.color: UM.Theme.getColor("quality_slider_unavailable")

                            UM.RecolorImage {
                                anchors.fill: parent
                                anchors.margins: 2 * screenScaleFactor
                                sourceSize.width: width
                                sourceSize.height: width
                                source: UM.Theme.getIcon(model.icon)
                                color: UM.Theme.getColor("quality_slider_unavailable")
                            }
                        }
                    }
                }

                //  Gradual Support Infill Checkbox
                CheckBox {
                    id: enableGradualInfillCheckBox
                    property alias _hovered: enableGradualInfillMouseArea.containsMouse

                    anchors.top: infillSlider.bottom
                    anchors.topMargin: UM.Theme.getSize("sidebar_margin").height / 2 // closer to slider since it belongs to the same category
                    anchors.left: infillCellRight.left

                    style: UM.Theme.styles.checkbox
                    enabled: base.settingsEnabled
                    visible: infillSteps.properties.enabled == "True"
                    checked: parseInt(infillSteps.properties.value) > 0

                    MouseArea {
                        id: enableGradualInfillMouseArea

                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: true

                        onClicked: {
                            infillSteps.setPropertyValue("value", (parseInt(infillSteps.properties.value) == 0) ? 5 : 0)
                            infillDensity.setPropertyValue("value", 90)
                        }

                        onEntered: {
                            base.showTooltip(enableGradualInfillCheckBox, Qt.point(-infillCellRight.x, 0),
                                catalog.i18nc("@label", "Gradual infill will gradually increase the amount of infill towards the top."))
                        }

                        onExited: {
                            base.hideTooltip()
                        }
                    }

                    Text {
                        id: gradualInfillLabel
                        anchors.left: enableGradualInfillCheckBox.right
                        anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width / 2
                        text: catalog.i18nc("@label", "Enable gradual")
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")
                    }
                }

                //  Infill list model for mapping icon
                ListModel
                {
                    id: infillModel
                    Component.onCompleted:
                    {
                        infillModel.append({
                            percentageMin: -1,
                            percentageMax: 0,
                            stepsMin: -1,
                            stepsMax: 0,
                            icon: "hollow"
                        })
                        infillModel.append({
                            percentageMin: 0,
                            percentageMax: 40,
                            stepsMin: -1,
                            stepsMax: 0,
                            icon: "sparse"
                        })
                        infillModel.append({
                            percentageMin: 40,
                            percentageMax: 89,
                            stepsMin: -1,
                            stepsMax: 0,
                            icon: "dense"
                        })
                        infillModel.append({
                            percentageMin: 90,
                            percentageMax: 9999999999,
                            stepsMin: -1,
                            stepsMax: 0,
                            icon: "solid"
                        })
                        infillModel.append({
                            percentageMin: 0,
                            percentageMax: 9999999999,
                            stepsMin: 1,
                            stepsMax: 9999999999,
                            icon: "gradual"
                        })
                    }
                }
            }

            //
            //  Enable support
            //
            Text
            {
                id: enableSupportLabel
                visible: enableSupportCheckBox.visible

                anchors.top: infillCellRight.bottom
                anchors.topMargin: UM.Theme.getSize("sidebar_margin").height * 1.5
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width
                anchors.verticalCenter: enableSupportCheckBox.verticalCenter

                text: catalog.i18nc("@label", "Generate Support");
                font: UM.Theme.getFont("default");
                color: UM.Theme.getColor("text");
            }

            CheckBox
            {
                id: enableSupportCheckBox
                property alias _hovered: enableSupportMouseArea.containsMouse

                anchors.top: enableSupportLabel.top
                anchors.left: infillCellRight.left

                style: UM.Theme.styles.checkbox;
                enabled: base.settingsEnabled

                visible: supportEnabled.properties.enabled == "True"
                checked: supportEnabled.properties.value == "True";

                MouseArea
                {
                    id: enableSupportMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    enabled: true
                    onClicked:
                    {
                        // The value is a string "True" or "False"
                        supportEnabled.setPropertyValue("value", supportEnabled.properties.value != "True");
                    }
                    onEntered:
                    {
                        base.showTooltip(enableSupportCheckBox, Qt.point(-enableSupportCheckBox.x, 0),
                            catalog.i18nc("@label", "Generate structures to support parts of the model which have overhangs. Without these structures, such parts would collapse during printing."));
                    }
                    onExited:
                    {
                        base.hideTooltip();
                    }
                }
            }

            Text
            {
                id: supportExtruderLabel
                visible: supportExtruderCombobox.visible
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width
                anchors.verticalCenter: supportExtruderCombobox.verticalCenter
                text: catalog.i18nc("@label", "Support Extruder");
                font: UM.Theme.getFont("default");
                color: UM.Theme.getColor("text");
            }

            ComboBox
            {
                id: supportExtruderCombobox
                visible: enableSupportCheckBox.visible && (supportEnabled.properties.value == "True") && (machineExtruderCount.properties.value > 1)
                model: extruderModel

                property string color_override: ""  // for manually setting values
                property string color:  // is evaluated automatically, but the first time is before extruderModel being filled
                {
                    var current_extruder = extruderModel.get(currentIndex);
                    color_override = "";
                    if (current_extruder === undefined) return ""
                    return (current_extruder.color) ? current_extruder.color : "";
                }

                textRole: "text"  // this solves that the combobox isn't populated in the first time Cura is started

                anchors.top: enableSupportCheckBox.bottom
                anchors.topMargin: ((supportEnabled.properties.value === "True") && (machineExtruderCount.properties.value > 1)) ? UM.Theme.getSize("sidebar_margin").height : 0
                anchors.left: infillCellRight.left

                width: UM.Theme.getSize("sidebar").width * .55
                height: ((supportEnabled.properties.value == "True") && (machineExtruderCount.properties.value > 1)) ? UM.Theme.getSize("setting_control").height : 0

                Behavior on height { NumberAnimation { duration: 100 } }

                style: UM.Theme.styles.combobox_color
                enabled: base.settingsEnabled
                property alias _hovered: supportExtruderMouseArea.containsMouse

                currentIndex: supportExtruderNr.properties !== null ? parseFloat(supportExtruderNr.properties.value) : 0
                onActivated:
                {
                    // Send the extruder nr as a string.
                    supportExtruderNr.setPropertyValue("value", String(index));
                }
                MouseArea
                {
                    id: supportExtruderMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    enabled: base.settingsEnabled
                    acceptedButtons: Qt.NoButton
                    onEntered:
                    {
                        base.showTooltip(supportExtruderCombobox, Qt.point(-supportExtruderCombobox.x, 0),
                            catalog.i18nc("@label", "Select which extruder to use for support. This will build up supporting structures below the model to prevent the model from sagging or printing in mid air."));
                    }
                    onExited:
                    {
                        base.hideTooltip();
                    }
                }

                function updateCurrentColor()
                {
                    var current_extruder = extruderModel.get(currentIndex);
                    if (current_extruder !== undefined) {
                        supportExtruderCombobox.color_override = current_extruder.color;
                    }
                }

            }

            Text
            {
                id: adhesionHelperLabel
                visible: adhesionCheckBox.visible

                text: catalog.i18nc("@label", "Build Plate Adhesion")
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
                elide: Text.ElideRight

                anchors {
                    left: parent.left
                    leftMargin: UM.Theme.getSize("sidebar_margin").width
                    right: infillCellLeft.right
                    rightMargin: UM.Theme.getSize("sidebar_margin").width
                    verticalCenter: adhesionCheckBox.verticalCenter
                }
            }

            CheckBox
            {
                id: adhesionCheckBox
                property alias _hovered: adhesionMouseArea.containsMouse

                anchors.top: enableSupportCheckBox.visible ? supportExtruderCombobox.bottom : infillCellRight.bottom
                anchors.topMargin: UM.Theme.getSize("sidebar_margin").height
                anchors.left: infillCellRight.left

                //: Setting enable printing build-plate adhesion helper checkbox
                style: UM.Theme.styles.checkbox;
                enabled: base.settingsEnabled

                visible: platformAdhesionType.properties.enabled == "True"
                checked: platformAdhesionType.properties.value != "skirt" && platformAdhesionType.properties.value != "none"

                MouseArea
                {
                    id: adhesionMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    enabled: base.settingsEnabled
                    onClicked:
                    {
                        var adhesionType = "skirt";
                        if(!parent.checked)
                        {
                            // Remove the "user" setting to see if the rest of the stack prescribes a brim or a raft
                            platformAdhesionType.removeFromContainer(0);
                            adhesionType = platformAdhesionType.properties.value;
                            if(adhesionType == "skirt" || adhesionType == "none")
                            {
                                // If the rest of the stack doesn't prescribe an adhesion-type, default to a brim
                                adhesionType = "brim";
                            }
                        }
                        platformAdhesionType.setPropertyValue("value", adhesionType);
                    }
                    onEntered:
                    {
                        base.showTooltip(adhesionCheckBox, Qt.point(-adhesionCheckBox.x, 0),
                            catalog.i18nc("@label", "Enable printing a brim or raft. This will add a flat area around or under your object which is easy to cut off afterwards."));
                    }
                    onExited:
                    {
                        base.hideTooltip();
                    }
                }
            }

            ListModel
            {
                id: extruderModel
                Component.onCompleted: populateExtruderModel()
            }

            //: Model used to populate the extrudelModel
            Cura.ExtrudersModel
            {
                id: extruders
                onModelChanged: populateExtruderModel()
            }

            Item
            {
                id: tipsCell
                anchors.top: adhesionCheckBox.visible ? adhesionCheckBox.bottom : (enableSupportCheckBox.visible ? supportExtruderCombobox.bottom : infillCellRight.bottom)
                anchors.topMargin: UM.Theme.getSize("sidebar_margin").height * 2
                anchors.left: parent.left
                width: parent.width
                height: tipsText.contentHeight * tipsText.lineCount

                Text
                {
                    id: tipsText
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width
                    anchors.right: parent.right
                    anchors.rightMargin: UM.Theme.getSize("sidebar_margin").width
                    anchors.top: parent.top
                    wrapMode: Text.WordWrap
                    text: catalog.i18nc("@label", "Need help improving your prints?<br>Read the <a href='%1'>Ultimaker Troubleshooting Guides</a>").arg("https://ultimaker.com/en/troubleshooting")
                    font: UM.Theme.getFont("default");
                    color: UM.Theme.getColor("text");
                    linkColor: UM.Theme.getColor("text_link")
                    onLinkActivated: Qt.openUrlExternally(link)
                }
            }

            UM.SettingPropertyProvider
            {
                id: infillExtruderNumber
                containerStackId: Cura.MachineManager.activeStackId
                key: "infill_extruder_nr"
                watchedProperties: [ "value" ]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: infillDensity
                containerStackId: Cura.MachineManager.activeStackId
                key: "infill_sparse_density"
                watchedProperties: [ "value" ]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: infillSteps
                containerStackId: Cura.MachineManager.activeStackId
                key: "gradual_infill_steps"
                watchedProperties: ["value", "enabled"]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: platformAdhesionType

                containerStackId: Cura.MachineManager.activeMachineId
                key: "adhesion_type"
                watchedProperties: [ "value", "enabled" ]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: supportEnabled

                containerStackId: Cura.MachineManager.activeMachineId
                key: "support_enable"
                watchedProperties: [ "value", "enabled", "description" ]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: machineExtruderCount

                containerStackId: Cura.MachineManager.activeMachineId
                key: "machine_extruder_count"
                watchedProperties: [ "value" ]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: supportExtruderNr

                containerStackId: Cura.MachineManager.activeMachineId
                key: "support_extruder_nr"
                watchedProperties: [ "value" ]
                storeIndex: 0
            }
        }
    }

    function populateExtruderModel()
    {
        extruderModel.clear();
        for(var extruderNumber = 0; extruderNumber < extruders.rowCount() ; extruderNumber++)
        {
            extruderModel.append({
                text: extruders.getItem(extruderNumber).name,
                color: extruders.getItem(extruderNumber).color
            })
        }
        supportExtruderCombobox.updateCurrentColor();
    }
}
