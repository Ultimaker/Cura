// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Window 2.1
import QtQuick.Controls.Styles 1.1

import UM 1.1 as UM
import Cura 1.0 as Cura
import ".."

Item
{
    id: base

    property string activeManufacturer: "Ultimaker";

    property variant wizard: null;

    Connections
    {
        target: base.wizard
        onNextClicked: //You can add functions here that get triggered when the final button is clicked in the wizard-element
        {
            var old_page_count = base.wizard.getPageCount()
            // Delete old pages (if any)
            for (var i = old_page_count - 1; i > 0; i--)
            {
                base.wizard.removePage(i)
            }
            saveMachine()
        }
        onBackClicked:
        {
            var old_page_count = base.wizard.getPageCount()
            // Delete old pages (if any)
            for (var i = old_page_count - 1; i > 0; i--)
            {
                base.wizard.removePage(i)
            }
        }
    }

    Label
    {
        id: title
        anchors.left: parent.left
        anchors.top: parent.top
        text: catalog.i18nc("@title", "Add Printer")
        font.pointSize: 18;
    }

    Label
    {
        id: subTitle
        anchors.left: parent.left
        anchors.top: title.bottom
        text: catalog.i18nc("@label", "Please select the type of printer:");
    }

    ScrollView
    {
        id: machinesHolder

        anchors{
            left: parent.left;
            top: subTitle.bottom;
            right: parent.right;
            bottom: machineNameHolder.top;
        }

        ListView
        {
            id: machineList

            model: UM.MachineDefinitionsModel { id: machineDefinitionsModel; showVariants: false; }
            focus: true

            section.property: "manufacturer"
            section.delegate: Button {
                text: section + " "
                style: ButtonStyle {
                    background: Rectangle {
                        id: manufacturerBackground
                        opacity: 0.3
                        border.width: 0
                        color: control.hovered ? palette.light : "transparent";
                        height: UM.Theme.sizes.standard_list_lineheight.height
                    }
                    label: Text {
                        horizontalAlignment: Text.AlignLeft
                        text: control.text
                        color: palette.windowText
                        font.bold: true
                        UM.RecolorImage {
                            id: downArrow
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.right
                            width: UM.Theme.sizes.standard_arrow.width
                            height: UM.Theme.sizes.standard_arrow.height
                            sourceSize.width: width
                            sourceSize.height: width
                            color: palette.windowText
                            source: base,activeManufacturer == section ? UM.Theme.icons.arrow_bottom : UM.Theme.icons.arrow_right
                        }
                    }
                }

                onClicked: {
                    base.activeManufacturer = section;
                    machineList.currentIndex = machineList.model.find("manufacturer", section)
                }
            }

            delegate: RadioButton {
                id: machineButton

                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.sizes.standard_list_lineheight.width

                opacity: 1;
                height: UM.Theme.sizes.standard_list_lineheight.height;

                checked: ListView.isCurrentItem;

                exclusiveGroup: printerGroup;

                text: model.name

                onClicked: {
                    ListView.view.currentIndex = index;
                    if(model.pages.length > 0) {
                        base.wizard.nextAvailable = true;
                    } else {
                        base.wizard.nextAvailable = false;
                    }
                }

                Label
                {
                    id: author
                    text: model.author;
                    anchors.left: machineButton.right
                    anchors.leftMargin: UM.Theme.sizes.standard_list_lineheight.height/2
                    anchors.verticalCenter: machineButton.verticalCenter
                    anchors.verticalCenterOffset: UM.Theme.sizes.standard_list_lineheight.height / 4
                    font: UM.Theme.fonts.caption;
                    color: palette.mid
                }

                states: State {
                    name: "collapsed";
                    when: base.activeManufacturer != model.manufacturer;

                    PropertyChanges { target: machineButton; opacity: 0; height: 0; }
                }

                transitions: [
                    Transition {
                        to: "collapsed";
                        SequentialAnimation {
                            NumberAnimation { property: "opacity"; duration: 75; }
                            NumberAnimation { property: "height"; duration: 75; }
                        }
                    },
                    Transition {
                        from: "collapsed";
                        SequentialAnimation {
                            NumberAnimation { property: "height"; duration: 75; }
                            NumberAnimation { property: "opacity"; duration: 75; }
                        }
                    }
                ]
            }
        }
    }

    Item
    {
        id: machineNameHolder
        height: childrenRect.height
        anchors.bottom: parent.bottom;
        Label
        {
            id: insertNameLabel
            text: catalog.i18nc("@label:textbox", "Printer Name:");
        }
        TextField
        {
            id: machineName;
            anchors.top: insertNameLabel.bottom
            text: machineList.model.getItem(machineList.currentIndex).name
            implicitWidth: UM.Theme.sizes.standard_list_input.width
        }
    }

    function saveMachine()
    {
        if(machineList.currentIndex != -1)
        {
            var item = machineList.model.getItem(machineList.currentIndex);
            machineList.model.createInstance(machineName.text, item.id)

            var pages = machineList.model.getItem(machineList.currentIndex).pages

            // Insert new pages (if any)
            for(var i = 0; i < pages.length; i++)
            {
                switch(pages[i]) {
                    case "SelectUpgradedParts":
                        base.wizard.appendPage(Qt.resolvedUrl("SelectUpgradedParts.qml"), catalog.i18nc("@title", "Select Upgraded Parts"));
                        break;
                    case "UpgradeFirmware":
                        base.wizard.appendPage(Qt.resolvedUrl("UpgradeFirmware.qml"), catalog.i18nc("@title", "Upgrade Firmware"));
                        break;
                    case "UltimakerCheckup":
                        base.wizard.appendPage(Qt.resolvedUrl("UltimakerCheckup.qml"), catalog.i18nc("@title", "Check Printer"));
                        break;
                    case "BedLeveling":
                        base.wizard.appendPage(Qt.resolvedUrl("Bedleveling.qml"), catalog.i18nc("@title", "Bed Levelling"));
                        break;
                    default:
                        base.wizard.appendPage(Qt.resolvedUrl("%1.qml".arg(pages[i])), pages[i])
                        break;
                }
            }
        }
    }

    ExclusiveGroup { id: printerGroup; }
    UM.I18nCatalog { id: catalog; name: "cura"; }
    SystemPalette { id: palette }
}
