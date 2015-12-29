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
        errorMessage.show = false
    }

    function editMachineName(word)
    {
        //Adds '#2' at the end or increases the number by 1 if the word ends with '#' and 1 or more digits
        var regEx = /[#][\d]+$///ends with '#' and then 1 or more digit
        var result = word.match(regEx)

        if (result != null)
        {
            result = result[0].split('')

            var numberString = ''
            for (var i = 1; i < result.length; i++){//starting at 1, makes it ignore the '#'
                numberString += result[i]
            }
            var newNumber = Number(numberString) + 1

            var newWord = word.replace(/[\d]+$/, newNumber)//replaces the last digits in the string by the same number + 1
            return newWord
        }
        else {
            return word + ' #2'
        }
    }

    function getMachineName()
    {
        var name = machineList.model.getItem(machineList.currentIndex).name

        //if the automatically assigned name is not unique, the editMachineName function keeps editing it untill it is.
        while (UM.MachineManager.checkInstanceExists(name) != false)
        {
            name = editMachineName(name)
        }
        return name
    }

    Connections
    {
        target: base.wizard
        onNextClicked: //You can add functions here that get triggered when the final button is clicked in the wizard-element
        {
            var name = machineName.text
            if (UM.MachineManager.checkInstanceExists(name) != false)
            {
                errorMessage.show = true
            }
            else
            {
                var old_page_count = base.wizard.getPageCount()
                // Delete old pages (if any)
                for (var i = old_page_count - 1; i > 0; i--)
                {
                    base.wizard.removePage(i)
                }
                saveMachine()
            }
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
                    machineName.text = getMachineName()
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
                    machineName.text = getMachineName()
                }

                Label
                {
                    id: author
                    text: model.author
                    font: UM.Theme.fonts.very_small
                    anchors.left: machineButton.right
                    anchors.leftMargin: UM.Theme.sizes.standard_list_lineheight.height/2
                    anchors.baseline: machineButton.baseline
                    anchors.baselineOffset: -UM.Theme.sizes.standard_list_lineheight.height / 16
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



    Column
    {
        id: machineNameHolder
        anchors.bottom: parent.bottom;
        //height: insertNameLabel.lineHeight * (2 + errorMessage.lineCount)

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
                color: UM.Theme.colors.error
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
            if(base.wizard.lastPage ==  true){
                base.wizard.visible = false
            }
        }
    }

    ExclusiveGroup { id: printerGroup; }
    UM.I18nCatalog { id: catalog; name: "cura"; }
    SystemPalette { id: palette }
}
