// Copyright (c) 2016 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Dialogs 1.2

import UM 1.2 as UM

UM.ManagementPage
{
    id: base;

    title: catalog.i18nc("@title:tab", "Materials");

    model: UM.InstanceContainersModel { filter: { "type": "material" } }
/*
    onAddObject: { var selectedMaterial = UM.MaterialManager.createProfile(); base.selectMaterial(selectedMaterial); }
    onRemoveObject: confirmDialog.open();
    onRenameObject: { renameDialog.open(); renameDialog.selectText(); }
*/
//     activateEnabled: false
    addEnabled: false
    removeEnabled: false
    renameEnabled: false

    scrollviewCaption: " "
    detailsVisible: true

    property string currency: UM.Preferences.getValue("general/currency")

    Item {
        UM.I18nCatalog { id: catalog; name: "cura"; }

        visible: base.currentItem != null
        anchors.fill: parent

        Label { id: profileName; text: base.currentItem ? base.currentItem.name : ""; font: UM.Theme.getFont("large"); width: parent.width; }

        TabView {
            id: scrollView
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: profileName.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.bottom: parent.bottom

            Tab {
                title: "Information"
                anchors.margins: UM.Theme.getSize("default_margin").height

                Column {
                    spacing: UM.Theme.getSize("default_margin").height

                    Grid {
                        id: containerGrid
                        columns: 2
                        spacing: UM.Theme.getSize("default_margin").width

                        Label { text: catalog.i18nc("@label", "Profile Type") }
                        Label { text: base.currentItem ? base.currentItem.metadata.status : "Unknown"}

                        Label { text: catalog.i18nc("@label", "Supplier") }
                        Label { text: base.currentItem ? base.currentItem.metadata.brand : "Unknown"}

                        Label { text: catalog.i18nc("@label", "Material Type") }
                        Label { text: base.currentItem ? base.currentItem.metadata.material : "Unknown" }

                        Label { text: catalog.i18nc("@label", "Color") }
                        Rectangle { color: base.currentItem ? base.currentItem.metadata.color_code : "yellow" }

                        Label { text: "<b>" + catalog.i18nc("@label", "Properties") + "</b>" }
                        Label { text: " " }

                        Label { text: catalog.i18nc("@label", "Density") }
                        Label { text: base.currentItem ? base.currentItem.metadata.properties.density + " " + "g/cm³" : "" }

                        Label { text: catalog.i18nc("@label", "Diameter") }
                        Label { text: base.currentItem ? base.currentItem.metadata.properties.diameter + " " + "mm" : ""}

                        Label {
                            text: catalog.i18nc("@label", "Filament cost")
                            height: spoolCostInput.height
                            verticalAlignment: Text.AlignVCenter
                        }

                        Row {
                            Label {
                                text: base.currentItem && base.currentItem.spoolCost ? base.currency + " " : ""
                                anchors.verticalCenter: parent.verticalCenter
                            }
                            TextField {
                                id: spoolCostInput
                                text: base.currentItem.spoolCost
                            }
                        }

                        Label { text: catalog.i18nc("@label", "Filament weight") }
                        Label { text: base.currentItem ? base.currentItem.metadata.properies.spool_weight + " " + "kg" : "" }

                        Label { text: catalog.i18nc("@label", "Filament length") }
                        Label { text: base.currentItem ? catalog.i18nc("@label", "approx.") + " " + base.currentItem.metadata.properties.spool_length + " " + "m" : "" }

                        Label { text: catalog.i18nc("@label", "Cost per meter") }
                        Label { text: base.currentItem && base.currentItem.lenghtCost ? catalog.i18nc("@label", "approx.") + " " + base.currency + " " + base.currentItem.lenghtCost + "/m" : "" }

//                         Column {
//
//
//
//
//                         }
//                         Column {
//
//
//
//                             Column {
//                                 Label { text: base.currentItem && base.currentItem.variant ? base.currentItem.variant : "" }
//                                 Row {
//                                     spacing: UM.Theme.getSize("default_margin").width/2
//                                     Rectangle {
//                                         color: base.currentItem && base.currentItem.colorDisplay ? base.currentItem.colorDisplay : "yellow"
//                                         width: colorLabel.height
//                                         height: colorLabel.height
//                                         border.width: UM.Theme.getSize("default_lining").height
//                                     }
//                                     Label { id: colorLabel; text: base.currentItem && base.currentItem.colorRAL ? base.currentItem.colorRAL : "" }
//                                 }
//                             }
//                         }
//                         Column {
//
//                         }
//                         Column {
//
//
//
//
//
//
//
//                         }
                    }
                    Label {
                        text: base.currentItem && base.currentItem.infoGeneral ? "<b>" + catalog.i18nc("@label", "Information") + "</b><br>" + base.currentItem.infoGeneral : ""
                        width: scrollView.width - 2 * UM.Theme.getSize("default_margin").width
                        wrapMode: Text.WordWrap
                    }
                    Label {
                        text: base.currentItem && base.currentItem.infoAdhesion ? "<b>" + catalog.i18nc("@label", "Adhesion") + "</b><br>" + base.currentItem.infoAdhesion : ""
                        width: scrollView.width - 2 * UM.Theme.getSize("default_margin").width
                        wrapMode: Text.WordWrap
                    }
                }
            }
            Tab {
                title: catalog.i18nc("@label", "Print settings")
                anchors.margins: UM.Theme.getSize("default_margin").height

                Grid {
                    columns: 2
                    spacing: UM.Theme.getSize("default_margin").width

                    Column {
                        Repeater {
                            model: base.currentItem ? base.currentItem.settings : null
                            Label {
                                text: modelData.name.toString();
                                elide: Text.ElideMiddle;
                            }
                        }
                    }
                    Column {
                        Repeater {
                            model: base.currentItem ? base.currentItem.settings : null
                            Label { text: modelData.value.toString() + " " + modelData.unit.toString(); }
                        }
                    }
                }
            }
        }
    }
}
