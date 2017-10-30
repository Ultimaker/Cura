// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.1 as UM
import Cura 1.0 as Cura

Item {
    id: base

    property bool activity: CuraApplication.platformActivity
    property string fileBaseName: ""

    UM.I18nCatalog { id: catalog; name:"cura"}

    height: childrenRect.height

    Connections
    {
        target: backgroundItem
        onHasMesh:
        {
            if (base.fileBaseName == "")
            {
                base.fileBaseName = name;
            }
        }
    }

    onActivityChanged: {
        if (activity == true && base.fileBaseName == ''){
            //this only runs when you open a file from the terminal (or something that works the same way; for example when you drag a file on the icon in MacOS or use 'open with' on Windows)
            base.fileBaseName = PrintInformation.baseName; //get the fileBaseName from PrintInformation.py because this saves the filebase when the file is opened using the terminal (or something alike)
            PrintInformation.setBaseName(base.fileBaseName);
        }
        if (activity == true && base.fileBaseName != ''){
            //this runs in all other cases where there is a mesh on the buildplate (activity == true). It uses the fileBaseName from the hasMesh signal
            PrintInformation.setBaseName(base.fileBaseName);
        }
        if (activity == false){
            //When there is no mesh in the buildplate; the printJobTextField is set to an empty string so it doesn't set an empty string as a jobName (which is later used for saving the file)
            PrintInformation.setBaseName('')
        }
    }

    Rectangle
    {
        id: jobNameRow
        anchors.top: parent.top
        anchors.right: parent.right
        height: UM.Theme.getSize("jobspecs_line").height
        visible: base.activity

        Item
        {
            width: parent.width
            height: parent.height

            Button
            {
                id: printJobPencilIcon
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                width: UM.Theme.getSize("save_button_specs_icons").width
                height: UM.Theme.getSize("save_button_specs_icons").height

                onClicked:
                {
                    printJobTextfield.selectAll();
                    printJobTextfield.focus = true;
                }
                style: ButtonStyle
                {
                    background: Item
                    {
                        UM.RecolorImage
                        {
                            width: UM.Theme.getSize("save_button_specs_icons").width;
                            height: UM.Theme.getSize("save_button_specs_icons").height;
                            sourceSize.width: width;
                            sourceSize.height: width;
                            color: control.hovered ? UM.Theme.getColor("text_scene_hover") : UM.Theme.getColor("text_scene");
                            source: UM.Theme.getIcon("pencil");
                        }
                    }
                }
            }

            TextField
            {
                id: printJobTextfield
                anchors.right: printJobPencilIcon.left
                anchors.rightMargin: UM.Theme.getSize("default_margin").width/2
                height: UM.Theme.getSize("jobspecs_line").height
                width: Math.max(__contentWidth + UM.Theme.getSize("default_margin").width, 50)
                maximumLength: 120
                property int unremovableSpacing: 5
                text: PrintInformation.jobName
                horizontalAlignment: TextInput.AlignRight
                onTextChanged: {
                    PrintInformation.setJobName(text);
                }
                onEditingFinished: {
                    if (printJobTextfield.text != ''){
                        printJobTextfield.focus = false;
                    }
                }
                validator: RegExpValidator {
                    regExp: /^[^\\ \/ \*\?\|\[\]]*$/
                }
                style: TextFieldStyle{
                    textColor: UM.Theme.getColor("text_scene");
                    font: UM.Theme.getFont("default_bold");
                    background: Rectangle {
                        opacity: 0
                        border.width: 0
                    }
                }
            }
        }
    }

    Label
    {
        id: boundingSpec
        anchors.top: jobNameRow.bottom
        anchors.right: parent.right
        height: UM.Theme.getSize("jobspecs_line").height
        verticalAlignment: Text.AlignVCenter
        font: UM.Theme.getFont("small")
        color: UM.Theme.getColor("text_scene")
        text: CuraApplication.getSceneBoundingBoxString
    }
}
