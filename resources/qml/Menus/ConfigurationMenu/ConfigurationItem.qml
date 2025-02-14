// Copyright (c) 2025 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.5 as UM
import Cura 1.0 as Cura

Button
{
    id: configurationItem

    property var configuration: null
    hoverEnabled: isValidMaterial && isValidCore

    property bool isValidMaterial:
    {
        if (configuration === null)
        {
            return false
        }
        var extruderConfigurations = configuration.extruderConfigurations

        for (var index in extruderConfigurations)
        {
            var name = extruderConfigurations[index].material ? extruderConfigurations[index].material.name : ""
            if (name == "" || name == "Unknown")
            {
                return false
            }
        }
        return true
    }

    property bool isValidCore:
    {
        if (configuration === null)
        {
            return false
        }
        var extruderConfigurations = configuration.extruderConfigurations
        var coresList = configuration.validCoresForPrinterType
        for (var index in extruderConfigurations)
        {
            var name = extruderConfigurations[index].hotendID ? extruderConfigurations[index].hotendID : ""
            if (name != "" && ! coresList.includes(name))
            {
                return false
            }
        }
        return true
    }

    background: Rectangle
    {
        color: parent.hovered ? UM.Theme.getColor("action_button_hovered") : UM.Theme.getColor("action_button")
        border.color: parent.checked ? UM.Theme.getColor("primary") : UM.Theme.getColor("lining")
        border.width: UM.Theme.getSize("default_lining").width
        radius: UM.Theme.getSize("default_radius").width
    }

    contentItem: Column
    {
        id: contentColumn
        width: parent.width
        padding: UM.Theme.getSize("default_margin").width
        spacing: UM.Theme.getSize("narrow_margin").height

        Row
        {
            id: extruderRow

            anchors
            {
                left: parent.left
                leftMargin: UM.Theme.getSize("default_margin").width
                right: parent.right
                rightMargin: UM.Theme.getSize("wide_margin").width
            }
            height: unknownMaterial.visible ? unknownMaterial.height : (repeater.count > 0 ? repeater.itemAt(0).height : 0)
            spacing: UM.Theme.getSize("default_margin").width

            Repeater
            {
                id: repeater
                model: configuration !== null ? configuration.extruderConfigurations: null
                width: parent.width
                delegate: PrintCoreConfiguration
                {
                    width: Math.round(parent.width / (configuration !== null ? configuration.extruderConfigurations.length : 1))
                    printCoreConfiguration: modelData
                    visible: configurationItem.isValidMaterial && configurationItem.isValidCore
                }
            }

            // Unknown material or core ('variant')
            Item
            {
                id: unknownMaterial
                height: unknownMaterialMessage.height
                width: parent.width

                anchors.top: parent.top

                visible: ! (configurationItem.isValidMaterial && configurationItem.isValidCore)

                UM.ColorImage
                {
                    id: icon
                    anchors.verticalCenter: unknownMaterialMessage.verticalCenter

                    source: UM.Theme.getIcon("Warning")
                    color: UM.Theme.getColor("warning")
                    width: UM.Theme.getSize("section_icon").width
                    height: width
                }

                UM.Label
                {
                    id: unknownMaterialMessage

                    function whenUnknownMaterial()
                    {
                        var extruderConfigurations = configuration.extruderConfigurations
                        var unknownMaterials = []
                        for (var index in extruderConfigurations)
                        {
                            var name = extruderConfigurations[index].material ? extruderConfigurations[index].material.name : ""
                            if (name == "" || name == "Unknown")
                            {
                                var materialType = extruderConfigurations[index].material.type
                                if (extruderConfigurations[index].material.type == "")
                                {
                                    materialType = "Unknown"
                                }

                                var brand = extruderConfigurations[index].material.brand
                                if (brand == "")
                                {
                                    brand = "Unknown"
                                }

                                name = materialType + " (" + brand + ")"
                                unknownMaterials.push(name)
                            }
                        }

                        unknownMaterials = "<b>" + unknownMaterials + "</b>"
                        var draftResult = catalog.i18nc("@label", "This configuration is not available because %1 is not recognized. Please visit %2 to download the correct material profile.");
                        return draftResult.arg(unknownMaterials).arg("<a href=' '>" + catalog.i18nc("@label","Marketplace") + "</a> ")
                    }

                    function whenMismatchedCore()
                    {
                        var extruderConfigurations = configuration.extruderConfigurations
                        var coresList = configuration.validCoresForPrinterType
                        var mismatchedCores = []
                        for (var index in extruderConfigurations)
                        {
                            var name = extruderConfigurations[index].hotendID ? extruderConfigurations[index].hotendID : ""
                            if (name != "" && ! coresList.includes(name))
                            {
                                mismatchedCores.push(name)
                            }
                        }

                        mismatchedCores = "<b>" + mismatchedCores + "</b>"
                        var draftResult = catalog.i18nc("@label", "This configuration is not available because there is a mismatch or other problem with core-type %1. Please visit <a href='%2'>the support page</a> to check which cores this printer-type supports w.r.t. new slices.");
                        return draftResult.arg(mismatchedCores).arg("https://support.ultimaker.com/s/article/1667411313529")
                    }

                    text:
                    {
                        if (configuration === null)
                        {
                            return ""
                        }

                        var extruderConfigurations = configuration.extruderConfigurations
                        var perExtruder = []
                        for (var index in extruderConfigurations)
                        {
                            var matName = extruderConfigurations[index].material ? extruderConfigurations[index].material.name : ""
                            var coreName = extruderConfigurations[index].hotendID ? extruderConfigurations[index].hotendID : ""
                            perExtruder.push(` [${coreName}/${matName}]`)
                        }

                        var configsStr = "<i>" + perExtruder + "</i>"
                        var warnStr = isValidMaterial ? whenMismatchedCore() : whenUnknownMaterial()
                        return configsStr + "<br/>" + warnStr
                    }
                    width: extruderRow.width

                    anchors.left: icon.right
                    anchors.right: unknownMaterial.right
                    anchors.leftMargin: UM.Theme.getSize("wide_margin").height
                    anchors.top: unknownMaterial.top

                    wrapMode: Text.WordWrap

                    onLinkActivated: (link) =>
                    {
                        if(link.trim().length === 0)
                        {
                            Cura.Actions.browsePackages.trigger();
                        }
                        else
                        {
                            Qt.openUrlExternally(link);
                        }
                    }
                }

                MouseArea
                {
                    anchors.fill: parent
                    cursorShape: unknownMaterialMessage.hoveredLink ? Qt.PointingHandCursor : Qt.ArrowCursor
                    acceptedButtons: Qt.NoButton
                }
            }
        }

        //Buildplate row separator
        Rectangle
        {
            id: separator

            visible: buildplateInformation.visible
            anchors
            {
                left: parent.left
                leftMargin: UM.Theme.getSize("wide_margin").width
                right: parent.right
                rightMargin: UM.Theme.getSize("wide_margin").width
            }
            height: visible ? Math.round(UM.Theme.getSize("default_lining").height / 2) : 0
            color: UM.Theme.getColor("lining")
        }

        Item
        {
            id: buildplateInformation

            anchors
            {
                left: parent.left
                leftMargin: UM.Theme.getSize("wide_margin").width
                right: parent.right
                rightMargin: UM.Theme.getSize("wide_margin").width
            }
            height: childrenRect.height
            visible: configuration !== null && configuration.buildplateConfiguration != "" && false //Buildplate is disabled as long as we have no printers that properly support buildplate swapping (so we can't test).

            // Show the type of buildplate. The first letter is capitalized
            Cura.IconWithText
            {
                id: buildplateLabel
                source: UM.Theme.getIcon("Buildplate")
                text:
                {
                    if (configuration === null)
                    {
                        return ""
                    }
                    return configuration.buildplateConfiguration.charAt(0).toUpperCase() + configuration.buildplateConfiguration.substr(1)
                }
                anchors.left: parent.left
            }
        }
    }

    Connections
    {
        target: Cura.MachineManager
        function onCurrentConfigurationChanged()
        {
            configurationItem.checked = Cura.MachineManager.matchesConfiguration(configuration)
        }
    }

    Component.onCompleted: configurationItem.checked = Cura.MachineManager.matchesConfiguration(configuration)

    onClicked:
    {
        if (isValidMaterial && isValidCore)
        {
            toggleContent()
            Cura.MachineManager.applyRemoteConfiguration(configuration)
        }
    }
}
