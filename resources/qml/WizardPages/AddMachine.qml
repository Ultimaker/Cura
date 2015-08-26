// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1
import QtQuick.Controls.Styles 1.1

import UM 1.0 as UM
import ".."

ColumnLayout
{
    id: wizardPage
    property string title
    property int pageWidth
    property int pageHeight
    property var manufacturers: wizardPage.lineManufacturers()
    property int manufacturerIndex: 0

    SystemPalette{id: palette}
    signal reloadModel(var newModel)

    width: wizardPage.pageWidth
    height: wizardPage.pageHeight

    Connections
    {
        target: elementRoot
        onNextClicked: //You can add functions here that get triggered when the final button is clicked in the wizard-element
        {
            saveMachine()
        }
    }

    function lineManufacturers(manufacturer)
    {
        var manufacturers = []
        for (var i = 0; i < UM.Models.availableMachinesModel.rowCount(); i++)
        {
            if (UM.Models.availableMachinesModel.getItem(i).manufacturer != manufacturers[manufacturers.length - 1])
            {
                manufacturers.push(UM.Models.availableMachinesModel.getItem(i).manufacturer)
            }
        }
        return manufacturers
    }

    Label
    {
        id: title
        anchors.left: parent.left
        anchors.top: parent.top
        text: parent.title
        font.pointSize: 18;
    }

    Label
    {
        id: subTitle
        anchors.left: parent.left
        anchors.top: title.bottom
        //: Add Printer wizard page description
        text: qsTr("Please select the type of printer:");
    }

    ScrollView
    {
        id: machinesHolder
        anchors.left: parent.left
        anchors.top: subTitle.bottom
        implicitWidth: wizardPage.width- UM.Theme.sizes.default_margin.width
        implicitHeight: wizardPage.height - subTitle.height - title.height - (machineNameHolder.height * 2)

        Component
        {
            id: machineDelegate
            ColumnLayout
            {
                id: machineLayout
                spacing: 0
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.sizes.standard_list_lineheight.width
                function showManufacturer()
                {
                    if (model.manufacturer == UM.Models.availableMachinesModel.getItem(index - 1).manufacturer){
                        return false
                    }
                    else{
                        return true
                    }
                }
                height:
                {
                    if (machineLayout.showManufacturer() & wizardPage.manufacturers[wizardPage.manufacturerIndex] == model.manufacturer)
                        return UM.Theme.sizes.standard_list_lineheight.height * 2
                    if (wizardPage.manufacturers[wizardPage.manufacturerIndex] == model.manufacturer | machineLayout.showManufacturer())
                         return UM.Theme.sizes.standard_list_lineheight.height * 1
                    else
                         return 0
                }
                Behavior on height
                {
                    NumberAnimation { target: machineLayout; property: "height"; duration: 200}
                }
                Button
                {
                    id: manufacturer
                    property color backgroundColor: "transparent"
                    height: UM.Theme.sizes.standard_list_lineheight.height
                    visible: machineLayout.showManufacturer()
                    anchors.top: machineLayout.top
                    anchors.topMargin: 0
                    text:
                    {
                        if (wizardPage.manufacturers[wizardPage.manufacturerIndex] == model.manufacturer)
                            return model.manufacturer + " ▼"
                        else
                            return model.manufacturer + " ►"
                    }
                    style: ButtonStyle
                    {
                        background: Rectangle
                        {
                            id: manufacturerBackground
                            opacity: 0.3
                            border.width: 0
                            color: manufacturer.backgroundColor
                            height: UM.Theme.sizes.standard_list_lineheight.height
                        }
                        label: Text
                        {
                            renderType: Text.NativeRendering
                            horizontalAlignment: Text.AlignLeft
                            text: control.text
                            color: palette.windowText
                            font.bold: true
                        }
                    }
                    MouseArea
                    {
                        id: mousearea
                        hoverEnabled: true
                        anchors.fill: parent
                        onEntered: manufacturer.backgroundColor = palette.light
                        onExited: manufacturer.backgroundColor = "transparent"
                        onClicked:
                        {
                            wizardPage.manufacturerIndex = wizardPage.manufacturers.indexOf(model.manufacturer)
                            machineList.currentIndex = index
                        }
                    }
                }

                RadioButton
                {
                    id: machineButton
                    opacity: wizardPage.manufacturers[wizardPage.manufacturerIndex] == model.manufacturer ? 1 : 0
                    height: wizardPage.manufacturers[wizardPage.manufacturerIndex] == model.manufacturer ? UM.Theme.sizes.standard_list_lineheight.height : 0
                    anchors.top: parent.top
                    anchors.topMargin: machineLayout.showManufacturer() ? manufacturer.height - 5 : 0
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.sizes.standard_list_lineheight.width
                    checked: machineList.currentIndex == index ? true : false
                    exclusiveGroup: printerGroup;
                    text: model.name
                    onClicked: machineList.currentIndex = index;
                    function getAnimationTime(time)
                    {
                        if (machineButton.opacity == 0)
                            return time
                        else
                            return 0
                    }
                    Label
                    {
                        id: author
                        visible: model.author != "Ultimaker" ? true : false
                        height: wizardPage.manufacturers[wizardPage.manufacturerIndex] == model.manufacturer ? UM.Theme.sizes.standard_list_lineheight.height : 0
                        //: Printer profile caption meaning: this profile is supported by the community
                        text: qsTr("community supported profile");
                        opacity: wizardPage.manufacturers[wizardPage.manufacturerIndex] == model.manufacturer ? 1 : 0
                        anchors.left: machineButton.right
                        anchors.leftMargin: UM.Theme.sizes.standard_list_lineheight.height/2
                        anchors.verticalCenter: machineButton.verticalCenter
                        anchors.verticalCenterOffset: UM.Theme.sizes.standard_list_lineheight.height / 4
                        font: UM.Theme.fonts.caption;
                        color: palette.mid
                    }
                    Behavior on opacity
                    {
                        SequentialAnimation
                        {
                            PauseAnimation { duration: machineButton.getAnimationTime(100) }
                            NumberAnimation { properties:"opacity"; duration: machineButton.getAnimationTime(200) }
                        }
                    }
                }

            }
        }

        ListView
        {
            id: machineList
            property int currentIndex: 0
            property int otherMachinesIndex:
            {
                for (var i = 0; i < UM.Models.availableMachinesModel.rowCount(); i++)
                {
                    if (UM.Models.availableMachinesModel.getItem(i).manufacturer != "Ultimaker")
                    {
                        return i
                    }
                }
            }
            anchors.fill: parent
            model: UM.Models.availableMachinesModel
            delegate: machineDelegate
            focus: true
        }
    }

    Item
    {
        id: machineNameHolder
        height: childrenRect.height
        anchors.top: machinesHolder.bottom
        Label
        {
            id: insertNameLabel
            //: Add Printer wizard field label
            text: qsTr("Printer Name:");
        }
        TextField
        {
            id: machineName;
            anchors.top: insertNameLabel.bottom
            text: machineList.model.getItem(machineList.currentIndex).name
            implicitWidth: UM.Theme.sizes.standard_list_input.width
        }
    }

    ExclusiveGroup { id: printerGroup; }


    function saveMachine()
    {
        if(machineList.currentIndex != -1)
        {
            UM.Models.availableMachinesModel.createMachine(machineList.currentIndex, machineName.text)
            var pages = UM.Models.availableMachinesModel.getItem(machineList.currentIndex).pages
            var old_page_count = elementRoot.getPageCount()
            for(var i = 0; i < UM.Models.count; i++)
            {
                print(UM.Models.getItem(i))
            }
            // Delete old pages (if any)
            for (var i = old_page_count - 1; i >  0; i--)
            {
                elementRoot.removePage(i)
                elementRoot.currentPage = 0
            }

            // Insert new pages (if any)
            for(var i = 0; i < pages.count; i++)
            {
                elementRoot.insertPage(pages.getItem(i).page + ".qml",pages.getItem(i).title,i + 1)
            }

            // Hack to ensure the current page is set correctly
            if(old_page_count == 1)
            {
                elementRoot.currentPage += 1
            }

            if (elementRoot.getPageCount() == elementRoot.currentPage)
            {
                elementRoot.visible = false
            }
        }
    }
}

