// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Window 2.1
import QtQuick.Controls.Styles 1.1

import UM 1.1 as UM

Item
{
    id: base

    property string activeManufacturer: "Ultimaker";

    property variant wizard: null;

    property bool visibility: base.wizard.visible
    onVisibilityChanged:
    {
        machineName.text = getMachineName()
    }

    function getMachineName()
    {
        var name = machineList.model.getItem(machineList.currentIndex).name

        return name
    }

    Connections
    {
        target: base.wizard
        onNextClicked: //You can add functions here that get triggered when the final button is clicked in the wizard-element
        {
            var name = machineName.text

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

        anchors
        {
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
                text: section
                style: ButtonStyle {
                    background: Rectangle {
                        border.width: 0
                        color: "transparent";
                        height: UM.Theme.getSize("standard_list_lineheight").height
                        width: machineList.width
                    }
                    label: Text {
                        anchors.left: parent.left
                        anchors.leftMargin: UM.Theme.getSize("standard_arrow").width + UM.Theme.getSize("default_margin").width
                        text: control.text
                        color: palette.windowText
                        font.bold: true
                        UM.RecolorImage {
                            id: downArrow
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.right: parent.left
                            anchors.rightMargin: UM.Theme.getSize("default_margin").width
                            width: UM.Theme.getSize("standard_arrow").width
                            height: UM.Theme.getSize("standard_arrow").height
                            sourceSize.width: width
                            sourceSize.height: width
                            color: palette.windowText
                            source: base.activeManufacturer == section ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_right")
                        }
                    }
                }

                onClicked: {
                    base.activeManufacturer = section;
                    machineList.currentIndex = machineList.model.find("manufacturer", section)
                    machineName.text = getMachineName()
                }
            }

            delegate: RadioButton {
                id: machineButton

                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("standard_list_lineheight").width

                opacity: 1;
                height: UM.Theme.getSize("standard_list_lineheight").height;

                checked: ListView.isCurrentItem;

                exclusiveGroup: printerGroup;

                text: model.name

                onClicked: {
                    ListView.view.currentIndex = index;
                    machineName.text = getMachineName()
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



    Column
    {
        id: machineNameHolder
        anchors.bottom: parent.bottom;

        Item
        {
            height: errorMessage.lineHeight
            anchors.bottom: insertNameLabel.top
            anchors.bottomMargin: insertNameLabel.height * errorMessage.lineCount
            Label
            {
                id: errorMessage
                property bool show: false
                width: base.width
                height: errorMessage.show ? errorMessage.lineHeight : 0
                visible: errorMessage.show
                text: catalog.i18nc("@label", "This printer name has already been used. Please choose a different printer name.");
                wrapMode: Text.WordWrap
                Behavior on height {NumberAnimation {duration: 75; }}
                color: UM.Theme.getColor("error")
            }
        }

        Label
        {
            id: insertNameLabel
            text: catalog.i18nc("@label:textbox", "Printer Name:");
        }
        TextField
        {
            id: machineName;
            text: getMachineName()
            implicitWidth: UM.Theme.getSize("standard_list_input").width
            maximumLength: 120
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
                    case "SelectUpgradedPartsUM2":
                        base.wizard.appendPage(Qt.resolvedUrl("SelectUpgradedPartsUM2.qml"), catalog.i18nc("@title", "Select Upgraded Parts"));
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
            if(base.wizard.lastPage ==  true){
                base.wizard.visible = false
            }
        }
    }

    ExclusiveGroup { id: printerGroup; }
    UM.I18nCatalog { id: catalog; name: "cura"; }
    SystemPalette { id: palette }
}
