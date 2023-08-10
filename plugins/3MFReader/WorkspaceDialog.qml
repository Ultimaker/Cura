// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtQuick.Window 2.2

import UM 1.5 as UM
import Cura 1.1 as Cura

UM.Dialog
{
    id: workspaceDialog
    title: catalog.i18nc("@title:window", "Open Project")

    margin: UM.Theme.getSize("default_margin").width
    minimumWidth: UM.Theme.getSize("modal_window_minimum").width
    minimumHeight: UM.Theme.getSize("modal_window_minimum").height

    backgroundColor: UM.Theme.getColor("detail_background")

    headerComponent: Rectangle
    {
        height: childrenRect.height + 2 * UM.Theme.getSize("default_margin").height
        color: UM.Theme.getColor("main_background")

        UM.Label
        {
            id: titleLabel
            text: catalog.i18nc("@action:title", "Summary - Cura Project")
            font: UM.Theme.getFont("large")
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.leftMargin: UM.Theme.getSize("default_margin").height
        }
    }

    Grid
    {
        columns: 20
        Repeater
        {
            model: {
                const icons = new Set();

                icons.add("Adhesion");
                icons.add("Anneal");
                icons.add("ArrowDoubleCircleRight");
                icons.add("ArrowDown");
                icons.add("ArrowFourWay");
                icons.add("ArrowLeft");
                icons.add("ArrowReset");
                icons.add("Bandage");
                icons.add("BlackMagic");
                icons.add("BlockGrid");
                icons.add("BlockSupportOverlaps");
                icons.add("Browser");
                icons.add("Bug");
                icons.add("Buildplate");
                icons.add("Cancel");
                icons.add("CancelBlock");
                icons.add("CancelCircle");
                icons.add("Certified");
                icons.add("Check");
                icons.add("CheckCircle");
                icons.add("ChevronSingleDown");
                icons.add("ChevronSingleLeft");
                icons.add("ChevronSingleRight");
                icons.add("ChevronSingleUp");
                icons.add("CircleMask");
                icons.add("CircleOutline");
                icons.add("Clock");
                icons.add("Cloud");
                icons.add("DocumentFilled");
                icons.add("Download");
                icons.add("DualExtrusion");
                icons.add("EmptyInfo");
                icons.add("Experiment");
                icons.add("Extruder");
                icons.add("ExtruderColor");
                icons.add("Eye");
                icons.add("Fan");
                icons.add("Folder");
                icons.add("FoodBeverages");
                icons.add("Formula");
                icons.add("Function");
                icons.add("GearCheck");
                icons.add("Globe");
                icons.add("Guide");
                icons.add("Hamburger");
                icons.add("Hammer");
                icons.add("Help");
                icons.add("House");
                icons.add("Infill0");
                icons.add("Infill1");
                icons.add("Infill2");
                icons.add("Infill3");
                icons.add("Infill100");
                icons.add("InfillGradual");
                icons.add("Information");
                icons.add("Knowledge");
                icons.add("Layers");
                icons.add("LayFlat");
                icons.add("LayFlatOnFace");
                icons.add("Library");
                icons.add("Lightning");
                icons.add("Link");
                icons.add("LinkExternal");
                icons.add("Magnifier");
                icons.add("MeshType");
                icons.add("MeshTypeIntersect");
                icons.add("MeshTypeNormal");
                icons.add("MeshTypeSupport");
                icons.add("Minus");
                icons.add("Mirror");
                icons.add("Nut");
                icons.add("Pen");
                icons.add("People");
                icons.add("Play");
                icons.add("Plugin");
                icons.add("Plus");
                icons.add("Printer");
                icons.add("PrinterTriple");
                icons.add("PrintQuality");
                icons.add("PrintShell");
                icons.add("PrintTopBottom");
                icons.add("PrintTravel");
                icons.add("PrintWalls");
                icons.add("Quick");
                icons.add("Rotate");
                icons.add("Save");
                icons.add("Scale");
                icons.add("ScaleMax");
                icons.add("Settings");
                icons.add("Shield");
                icons.add("Shop");
                icons.add("ShoppingCart");
                icons.add("Sliders");
                icons.add("Solid");
                icons.add("Speak");
                icons.add("SpeedOMeter");
                icons.add("Spinner");
                icons.add("Spool");
                icons.add("Sputnik");
                icons.add("Star");
                icons.add("StarFilled");
                icons.add("Support");
                icons.add("SupportBlocker");
                icons.add("ThreeDots");
                icons.add("UltimakerCura");
                icons.add("View3D");
                icons.add("ViewFront");
                icons.add("ViewLeft");
                icons.add("ViewRight");
                icons.add("ViewTop");
                icons.add("Visual");
                icons.add("Warning");

                icons.add("Adhesion copy");
                icons.add("Anneal copy");
                icons.add("ArrowDoubleCircleRight copy");
                icons.add("ArrowDown copy");
                icons.add("ArrowFourWay copy");
                icons.add("ArrowLeft copy");
                icons.add("ArrowReset copy");
                icons.add("Bandage copy");
                icons.add("BlackMagic copy");
                icons.add("BlockGrid copy");
                icons.add("BlockSupportOverlaps copy");
                icons.add("Browser copy");
                icons.add("Bug copy");
                icons.add("Buildplate copy");
                icons.add("Cancel copy");
                icons.add("CancelBlock copy");
                icons.add("CancelCircle copy");
                icons.add("Certified copy");
                icons.add("Check copy");
                icons.add("CheckCircle copy");
                icons.add("ChevronSingleDown copy");
                icons.add("ChevronSingleLeft copy");
                icons.add("ChevronSingleRight copy");
                icons.add("ChevronSingleUp copy");
                icons.add("CircleMask copy");
                icons.add("CircleOutline copy");
                icons.add("Clock copy");
                icons.add("Cloud copy");
                icons.add("DocumentFilled copy");
                icons.add("Download copy");
                icons.add("DualExtrusion copy");
                icons.add("EmptyInfo copy");
                icons.add("Experiment copy");
                icons.add("Extruder copy");
                icons.add("ExtruderColor copy");
                icons.add("Eye copy");
                icons.add("Fan copy");
                icons.add("Folder copy");
                icons.add("FoodBeverages copy");
                icons.add("Formula copy");
                icons.add("Function copy");
                icons.add("GearCheck copy");
                icons.add("Globe copy");
                icons.add("Guide copy");
                icons.add("Hamburger copy");
                icons.add("Hammer copy");
                icons.add("Help copy");
                icons.add("House copy");
                icons.add("Infill0 copy");
                icons.add("Infill1 copy");
                icons.add("Infill2 copy");
                icons.add("Infill3 copy");
                icons.add("Infill100 copy");
                icons.add("InfillGradual copy");
                icons.add("Information copy");
                icons.add("Knowledge copy");
                icons.add("Layers copy");
                icons.add("LayFlat copy");
                icons.add("LayFlatOnFace copy");
                icons.add("Library copy");
                icons.add("Lightning copy");
                icons.add("Link copy");
                icons.add("LinkExternal copy");
                icons.add("Magnifier copy");
                icons.add("MeshType copy");
                icons.add("MeshTypeIntersect copy");
                icons.add("MeshTypeNormal copy");
                icons.add("MeshTypeSupport copy");
                icons.add("Minus copy");
                icons.add("Mirror copy");
                icons.add("Nut copy");
                icons.add("Pen copy");
                icons.add("People copy");
                icons.add("Play copy");
                icons.add("Plugin copy");
                icons.add("Plus copy");
                icons.add("Printer copy");
                icons.add("PrinterTriple copy");
                icons.add("PrintQuality copy");
                icons.add("PrintShell copy");
                icons.add("PrintTopBottom copy");
                icons.add("PrintTravel copy");
                icons.add("PrintWalls copy");
                icons.add("Quick copy");
                icons.add("Rotate copy");
                icons.add("Save copy");
                icons.add("Scale copy");
                icons.add("ScaleMax copy");
                icons.add("Settings copy");
                icons.add("Shield copy");
                icons.add("Shop copy");
                icons.add("ShoppingCart copy");
                icons.add("Sliders copy");
                icons.add("Solid copy");
                icons.add("Speak copy");
                icons.add("SpeedOMeter copy");
                icons.add("Spinner copy");
                icons.add("Spool copy");
                icons.add("Sputnik copy");
                icons.add("Star copy");
                icons.add("StarFilled copy");
                icons.add("Support copy");
                icons.add("SupportBlocker copy");
                icons.add("ThreeDots copy");
                icons.add("UltimakerCura copy");
                icons.add("View3D copy");
                icons.add("ViewFront copy");
                icons.add("ViewLeft copy");
                icons.add("ViewRight copy");
                icons.add("ViewTop copy");
                icons.add("Visual copy");
                icons.add("Warning copy");

                icons.add("Adhesion copy 2");
                icons.add("Anneal copy 2");
                icons.add("ArrowDoubleCircleRight copy 2");
                icons.add("ArrowDown copy 2");
                icons.add("ArrowFourWay copy 2");
                icons.add("ArrowLeft copy 2");
                icons.add("ArrowReset copy 2");
                icons.add("Bandage copy 2");
                icons.add("BlackMagic copy 2");
                icons.add("BlockGrid copy 2");
                icons.add("BlockSupportOverlaps copy 2");
                icons.add("Browser copy 2");
                icons.add("Bug copy 2");
                icons.add("Buildplate copy 2");
                icons.add("Cancel copy 2");
                icons.add("CancelBlock copy 2");
                icons.add("CancelCircle copy 2");
                icons.add("Certified copy 2");
                icons.add("Check copy 2");
                icons.add("CheckCircle copy 2");
                icons.add("ChevronSingleDown copy 2");
                icons.add("ChevronSingleLeft copy 2");
                icons.add("ChevronSingleRight copy 2");
                icons.add("ChevronSingleUp copy 2");
                icons.add("CircleMask copy 2");
                icons.add("CircleOutline copy 2");
                icons.add("Clock copy 2");
                icons.add("Cloud copy 2");
                icons.add("DocumentFilled copy 2");
                icons.add("Download copy 2");
                icons.add("DualExtrusion copy 2");
                icons.add("EmptyInfo copy 2");
                icons.add("Experiment copy 2");
                icons.add("Extruder copy 2");
                icons.add("ExtruderColor copy 2");
                icons.add("Eye copy 2");
                icons.add("Fan copy 2");
                icons.add("Folder copy 2");
                icons.add("FoodBeverages copy 2");
                icons.add("Formula copy 2");
                icons.add("Function copy 2");
                icons.add("GearCheck copy 2");
                icons.add("Globe copy 2");
                icons.add("Guide copy 2");
                icons.add("Hamburger copy 2");
                icons.add("Hammer copy 2");
                icons.add("Help copy 2");
                icons.add("House copy 2");
                icons.add("Infill0 copy 2");
                icons.add("Infill1 copy 2");
                icons.add("Infill2 copy 2");
                icons.add("Infill3 copy 2");
                icons.add("Infill100 copy 2");
                icons.add("InfillGradual copy 2");
                icons.add("Information copy 2");
                icons.add("Knowledge copy 2");
                icons.add("Layers copy 2");
                icons.add("LayFlat copy 2");
                icons.add("LayFlatOnFace copy 2");
                icons.add("Library copy 2");
                icons.add("Lightning copy 2");
                icons.add("Link copy 2");
                icons.add("LinkExternal copy 2");
                icons.add("Magnifier copy 2");
                icons.add("MeshType copy 2");
                icons.add("MeshTypeIntersect copy 2");
                icons.add("MeshTypeNormal copy 2");
                icons.add("MeshTypeSupport copy 2");
                icons.add("Minus copy 2");
                icons.add("Mirror copy 2");
                icons.add("Nut copy 2");
                icons.add("Pen copy 2");
                icons.add("People copy 2");
                icons.add("Play copy 2");
                icons.add("Plugin copy 2");
                icons.add("Plus copy 2");
                icons.add("Printer copy 2");
                icons.add("PrinterTriple copy 2");
                icons.add("PrintQuality copy 2");
                icons.add("PrintShell copy 2");
                icons.add("PrintTopBottom copy 2");
                icons.add("PrintTravel copy 2");
                icons.add("PrintWalls copy 2");
                icons.add("Quick copy 2");
                icons.add("Rotate copy 2");
                icons.add("Save copy 2");
                icons.add("Scale copy 2");
                icons.add("ScaleMax copy 2");
                icons.add("Settings copy 2");
                icons.add("Shield copy 2");
                icons.add("Shop copy 2");
                icons.add("ShoppingCart copy 2");
                icons.add("Sliders copy 2");
                icons.add("Solid copy 2");
                icons.add("Speak copy 2");
                icons.add("SpeedOMeter copy 2");
                icons.add("Spinner copy 2");
                icons.add("Spool copy 2");
                icons.add("Sputnik copy 2");
                icons.add("Star copy 2");
                icons.add("StarFilled copy 2");
                icons.add("Support copy 2");
                icons.add("SupportBlocker copy 2");
                icons.add("ThreeDots copy 2");
                icons.add("UltimakerCura copy 2");
                icons.add("View3D copy 2");
                icons.add("ViewFront copy 2");
                icons.add("ViewLeft copy 2");
                icons.add("ViewRight copy 2");
                icons.add("ViewTop copy 2");
                icons.add("Visual copy 2");
                icons.add("Warning copy 2");


                icons.add("Warning");
                icons.add("Information");
                icons.add("Plus");
                icons.add("Minus");
                icons.add("Printer");
                icons.add("Certificate");
                icons.add("Cancel");
                icons.add("Spool");
                icons.add("UltimakerCura");
                icons.add("Information");
                icons.add("Information");
                icons.add("Plus");
                icons.add("Cancel");
                icons.add("UltimakerCura");
                icons.add("Printer");
                icons.add("Spool");
                icons.add("Sliders");
                icons.add("Plugin");
                icons.add("LinkExternal");
                icons.add("ChevronSingleUp");
                icons.add("ChevronSingleDown");
                icons.add("ChevronSingleRight");
                icons.add("Infill0");
                icons.add("MeshTypeSupport");
                icons.add("MeshTypeIntersect");
                icons.add("BlockSupportOverlaps");
                icons.add("Minus");
                icons.add("Folder");
                icons.add("Extruder");
                icons.add("Adhesion");
                icons.add("Printer");
                icons.add("PrintQuality");
                icons.add("PrintShell");
                icons.add("PrintTopBottom");
                icons.add("Infill1");
                icons.add("SpeedOMeter");
                icons.add("PrintTravel");
                icons.add("Fan");
                icons.add("Support");
                icons.add("DualExtrusion");
                icons.add("Bandage");
                icons.add("BlackMagic");
                icons.add("Experiment");
                icons.add("CircleOutline");
                icons.add("ArrowDoubleCircleRight");
                icons.add("CheckCircle");
                icons.add("Warning");
                icons.add("Clock");
                icons.add("Spool");
                icons.add("Warning");
                icons.add("Check");
                icons.add("StarFilled");
                icons.add("Pen");
                icons.add("Guide");
                icons.add("StarFilled");
                icons.add("Star");
                icons.add("ThreeDots");
                icons.add("InfillGradual");
                icons.add("Infill0");
                icons.add("Infill3");
                icons.add("Infill2");
                icons.add("Solid");
                icons.add("ArrowReset");
                icons.add("ChevronSingleLeft");
                icons.add("House");
                icons.add("PrinterTriple");
                icons.add("Function");
                icons.add("Magnifier");
                icons.add("Hamburger");
                icons.add("View3D");
                icons.add("Layers");
                icons.add("ViewFront");
                icons.add("ViewTop");
                icons.add("ViewLeft");
                icons.add("ViewRight");
                icons.add("Plugin");
                icons.add("Spool");
                icons.add("Dot");
                icons.add("Mirror");
                icons.add("ArrowReset");
                icons.add("LayFlat");
                icons.add("LayFlatOnFace");
                icons.add("Rotate");
                icons.add("ArrowReset");
                icons.add("Scale");
                icons.add("ArrowFourWay");
                icons.add("Buildplate");
                icons.add("PrintQuality");
                icons.add("Shield");
                icons.add("Sputnik");
                icons.add("CancelBlock");
                icons.add("ChevronSingleDown");
                icons.add("People");
                icons.add("Link");
                icons.add("Play");
                icons.add("Clock");
                icons.add("CloudBadge");
                icons.add("CloudBadge");
                icons.add("CheckBlueBG");
                icons.add("Sliders");
                icons.add("Quick");
                icons.add("ScaleMax");
                icons.add("MeshType");
                icons.add("Star");
                icons.add("StarFilled");
                icons.add("PrintQuality");
                icons.add("CancelBlock");
                icons.add("Infill0");
                icons.add("Eye");

                const images = new Set();
                images.add("3d_printer_faded");
                images.add("add_printer");
                images.add("cura_connected_printers");
                images.add("first_run_machine_types");
                images.add("first_run_material_usage");
                images.add("first_run_number_slices");
                images.add("first_run_print_settings");
                images.add("first_run_ultimaker_cloud");
                images.add("header_pattern");
                images.add("insert_usb");
                images.add("logo");
                images.add("material_ecosystem");
                images.add("third_party_printer");
                images.add("ultimaker_printer");
                images.add("welcome_cura");

                const icon_srcs = Array.from(icons).map((icon_src) => UM.Theme.getIcon(icon_src));
                const image_srcs = Array.from(images).map((image_src) => UM.Theme.getImage(image_src));
                console.log("icon_srcs.length", icon_srcs.length);
                console.log("image_srcs.length", image_srcs.length);
                return icon_srcs.concat(image_srcs);
            }
            delegate: UM.ColorImage
            {
                source: modelData
                width: 30
                height: 30
            }
        }
    }

    Rectangle
    {
        visible: false
        anchors.fill: parent
        UM.I18nCatalog { id: catalog; name: "cura" }
        color: UM.Theme.getColor("main_background")

        Flickable
        {
            id: dialogSummaryItem
            width: parent.width
            height: parent.height

            clip: true

            contentHeight: contentColumn.height
            ScrollBar.vertical: UM.ScrollBar { id: scrollbar }

            ListModel
            {
                id: resolveStrategiesModel
                // Instead of directly adding the list elements, we add them afterwards.
                // This is because it's impossible to use setting function results to be bound to listElement properties directly.
                // See http://stackoverflow.com/questions/7659442/listelement-fields-as-properties
                Component.onCompleted:
                {
                    append({"key": "override", "label": catalog.i18nc("@action:ComboBox Update/override existing profile", "Update existing")});
                    append({"key": "new", "label": catalog.i18nc("@action:ComboBox Save settings in a new profile", "Create new")});
                }
            }

            Column
            {
                id: contentColumn
                width: parent.width - scrollbar.width - UM.Theme.getSize("default_margin").width
                height: childrenRect.height

                spacing: UM.Theme.getSize("default_margin").height
                leftPadding: UM.Theme.getSize("default_margin").width
                rightPadding: UM.Theme.getSize("default_margin").width

                WorkspaceSection
                {
                    id: printerSection
                    title: catalog.i18nc("@action:label", "Printer settings")
                    iconSource: UM.Theme.getIcon("Printer")
                    content: Column
                    {
                        spacing: UM.Theme.getSize("default_margin").height
                        leftPadding: UM.Theme.getSize("medium_button_icon").width + UM.Theme.getSize("default_margin").width

                        WorkspaceRow
                        {
                            leftLabelText: catalog.i18nc("@action:label", "Type")
                            rightLabelText: manager.machineType
                        }

                        WorkspaceRow
                        {
                            leftLabelText: catalog.i18nc("@action:label", manager.isPrinterGroup ? "Printer Group" : "Printer Name")
                            rightLabelText: manager.machineName == catalog.i18nc("@button", "Create new") ? "" : manager.machineName
                        }
                    }

                    comboboxTitle: catalog.i18nc("@action:label", "Open With")
                    comboboxTooltipText: catalog.i18nc("@info:tooltip", "Printer settings will be updated to match the settings saved with the project.")
                    comboboxVisible: workspaceDialog.visible && manager.updatableMachinesModel.count > 1
                    combobox: Cura.MachineSelector
                    {
                        id: machineSelector
                        headerCornerSide: Cura.RoundedRectangle.Direction.All
                        width: parent.width
                        height: parent.height
                        machineListModel: manager.updatableMachinesModel
                        machineName: manager.machineName

                        isConnectedCloudPrinter: false
                        isCloudRegistered: false
                        isNetworkPrinter: manager.isNetworked
                        isGroup: manager.isAbstractMachine
                        connectionStatus: ""

                        minDropDownWidth: machineSelector.width

                        buttons: [
                            Cura.SecondaryButton
                            {
                                id: createNewPrinter
                                text: catalog.i18nc("@button", "Create new")
                                fixedWidthMode: true
                                width: parent.width - leftPadding * 1.5
                                onClicked:
                                {
                                    toggleContent()
                                    manager.setResolveStrategy("machine", "new")
                                    machineSelector.machineName = catalog.i18nc("@button", "Create new")
                                    manager.setIsAbstractMachine(false)
                                    manager.setIsNetworkedMachine(false)
                                }
                            }
                        ]

                        onSelectPrinter: function(machine)
                        {
                            toggleContent();
                            machineSelector.machineName = machine.name
                            manager.setResolveStrategy("machine", "override")
                            manager.setMachineToOverride(machine.id)
                            manager.setIsAbstractMachine(machine.isAbstractMachine)
                            manager.setIsNetworkedMachine(machine.isNetworked)
                        }
                    }
                }

                WorkspaceSection
                {
                    id: profileSection
                    title: catalog.i18nc("@action:label", "Profile settings")
                    iconSource: UM.Theme.getIcon("Sliders")
                    content: Column
                    {
                        id: profileSettingsValuesTable
                        spacing: UM.Theme.getSize("default_margin").height
                        leftPadding: UM.Theme.getSize("medium_button_icon").width + UM.Theme.getSize("default_margin").width

                        WorkspaceRow
                        {
                            leftLabelText: catalog.i18nc("@action:label", "Name")
                            rightLabelText: manager.qualityName
                        }

                        WorkspaceRow
                        {
                            leftLabelText: catalog.i18nc("@action:label", "Intent")
                            rightLabelText: manager.intentName
                        }

                        WorkspaceRow
                        {
                            leftLabelText: catalog.i18nc("@action:label", "Not in profile")
                            rightLabelText: catalog.i18ncp("@action:label", "%1 override", "%1 overrides", manager.numUserSettings).arg(manager.numUserSettings)
                            visible: manager.numUserSettings != 0
                        }

                        WorkspaceRow
                        {
                            leftLabelText: catalog.i18nc("@action:label", "Derivative from")
                            rightLabelText: catalog.i18ncp("@action:label", "%1, %2 override", "%1, %2 overrides", manager.numSettingsOverridenByQualityChanges).arg(manager.qualityType).arg(manager.numSettingsOverridenByQualityChanges)
                            visible: manager.numSettingsOverridenByQualityChanges != 0
                        }
                    }

                    comboboxVisible: manager.qualityChangesConflict
                    combobox: Cura.ComboBox
                    {
                        id: qualityChangesResolveComboBox
                        model: resolveStrategiesModel
                        textRole: "label"
                        visible: manager.qualityChangesConflict
                        contentLeftPadding: UM.Theme.getSize("default_margin").width + UM.Theme.getSize("narrow_margin").width
                        textFont: UM.Theme.getFont("medium")

                        background: Cura.RoundedRectangle
                        {
                            border.width: UM.Theme.getSize("default_lining").width
                            border.color: UM.Theme.getColor("lining")
                            color: qualityChangesResolveComboBox.hovered ? UM.Theme.getColor("expandable_hover") : UM.Theme.getColor("action_button")
                            cornerSide: Cura.RoundedRectangle.Direction.All
                            radius: UM.Theme.getSize("default_radius").width
                        }

                        // This is a hack. This will trigger onCurrentIndexChanged and set the index when this component in loaded
                        currentIndex:
                        {
                            currentIndex = 0
                        }

                        onCurrentIndexChanged:
                        {
                            manager.setResolveStrategy("quality_changes", resolveStrategiesModel.get(currentIndex).key)
                        }
                    }
                }

                WorkspaceSection
                {
                    id: materialSection
                    title: catalog.i18nc("@action:label", "Material settings")
                    iconSource: UM.Theme.getIcon("Spool")
                    content: Column
                    {
                        spacing: UM.Theme.getSize("default_margin").height
                        leftPadding: UM.Theme.getSize("medium_button_icon").width + UM.Theme.getSize("default_margin").width

                        Repeater
                        {
                            model: manager.materialLabels
                            delegate: WorkspaceRow
                            {
                                leftLabelText: catalog.i18nc("@action:label", "Name")
                                rightLabelText: modelData
                            }
                        }
                    }

                    comboboxVisible: manager.materialConflict

                    combobox: Cura.ComboBox
                    {
                        id: materialResolveComboBox
                        model: resolveStrategiesModel
                        textRole: "label"
                        visible: manager.materialConflict
                        contentLeftPadding: UM.Theme.getSize("default_margin").width + UM.Theme.getSize("narrow_margin").width
                        textFont: UM.Theme.getFont("medium")

                        background: Cura.RoundedRectangle
                        {
                            border.width: UM.Theme.getSize("default_lining").width
                            border.color: UM.Theme.getColor("lining")
                            color: materialResolveComboBox.hovered ? UM.Theme.getColor("expandable_hover") : UM.Theme.getColor("action_button")
                            cornerSide: Cura.RoundedRectangle.Direction.All
                            radius: UM.Theme.getSize("default_radius").width
                        }

                        // This is a hack. This will trigger onCurrentIndexChanged and set the index when this component in loaded
                        currentIndex:
                        {
                            currentIndex = 0
                        }

                        onCurrentIndexChanged:
                        {
                            manager.setResolveStrategy("material", resolveStrategiesModel.get(currentIndex).key)
                        }
                    }
                }

                WorkspaceSection
                {
                    id: visibilitySection
                    title: catalog.i18nc("@action:label", "Setting visibility")
                    iconSource: UM.Theme.getIcon("Eye")
                    content: Column
                    {
                        spacing: UM.Theme.getSize("default_margin").height
                        leftPadding: UM.Theme.getSize("medium_button_icon").width + UM.Theme.getSize("default_margin").width
                        bottomPadding: UM.Theme.getSize("narrow_margin").height

                        WorkspaceRow
                        {
                            leftLabelText: catalog.i18nc("@action:label", "Mode")
                            rightLabelText: manager.activeMode
                        }

                        WorkspaceRow
                        {
                            leftLabelText: catalog.i18nc("@action:label", "%1 out of %2" ).arg(manager.numVisibleSettings).arg(manager.totalNumberOfSettings)
                            rightLabelText: manager.activeMode
                            visible: manager.hasVisibleSettingsField
                        }
                    }
                }

                Row
                {
                    id: clearBuildPlateWarning
                    width: parent.width
                    height: childrenRect.height
                    spacing: UM.Theme.getSize("default_margin").width
                    visible: manager.hasObjectsOnPlate

                    UM.ColorImage
                    {
                        width: warningLabel.height
                        height: width
                        source: UM.Theme.getIcon("Information")
                        color: UM.Theme.getColor("text")
                    }
                    UM.Label
                    {
                        id: warningLabel
                        text: catalog.i18nc("@action:warning", "Loading a project will clear all models on the build plate.")
                    }
                }
            }
        }
    }

    property bool warning: manager.missingPackages.length > 0

    footerComponent: Rectangle
    {
        color: warning ? UM.Theme.getColor("warning") : "transparent"
        anchors.bottom: parent.bottom
        width: parent.width
        height: childrenRect.height + (warning ? 2 * workspaceDialog.margin : workspaceDialog.margin)

        Column
        {
            height: childrenRect.height
            spacing: workspaceDialog.margin

            anchors.leftMargin: workspaceDialog.margin
            anchors.rightMargin: workspaceDialog.margin
            anchors.bottomMargin: workspaceDialog.margin
            anchors.topMargin: warning ? workspaceDialog.margin : 0

            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top

            RowLayout
            {
                id: warningRow
                height: childrenRect.height
                visible: warning
                spacing: workspaceDialog.margin
                UM.ColorImage
                {
                    width: UM.Theme.getSize("extruder_icon").width
                    height: UM.Theme.getSize("extruder_icon").height
                    source: UM.Theme.getIcon("Warning")
                }

                UM.Label
                {
                    id: warningText
                    text: catalog.i18nc("@label", "The material used in this project is currently not installed in Cura.<br/>Install the material profile and reopen the project.")
                }
            }

            Loader
            {
                width: parent.width
                height: childrenRect.height
                sourceComponent: buttonRow
            }
        }
    }

    buttonSpacing: UM.Theme.getSize("wide_margin").width

    rightButtons: [
        Cura.TertiaryButton
        {
            visible: !warning
            text: catalog.i18nc("@action:button", "Cancel")
            onClicked: reject()
        },
        Cura.PrimaryButton
        {
            visible: !warning
            text: catalog.i18nc("@action:button", "Open")
            onClicked: accept()
        },
        Cura.TertiaryButton
        {
            visible: warning
            text: catalog.i18nc("@action:button", "Open project anyway")
            onClicked: {
                manager.showMissingMaterialsWarning();
                accept();
            }
        },
        Cura.PrimaryButton
        {
            visible: warning
            text: catalog.i18nc("@action:button", "Install missing material")
            onClicked: manager.installMissingPackages()
        }
    ]

    onClosing: manager.notifyClosed()
    onRejected: manager.onCancelButtonClicked()
    onAccepted: manager.onOkButtonClicked()
    onVisibleChanged:
    {
        if (visible)
        {
            // Force relead the comboboxes
            // Since this dialog is only created once the first time you open it, these comboxes need to be reloaded
            // each time it is shown after the first time so that the indexes will update correctly.
            materialSection.reloadValues()
            profileSection.reloadValues()
            printerSection.reloadValues()
        }
    }
}
