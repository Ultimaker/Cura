// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.1 as UM

UM.PreferencesPage
{
    //: General configuration page title
    title: catalog.i18nc("@title","General");

    function reset()
    {
        UM.Preferences.resetPreference("general/language")
        UM.Preferences.resetPreference("physics/automatic_push_free")
        UM.Preferences.resetPreference("mesh/scale_to_fit")
        UM.Preferences.resetPreference("info/send_slice_info")
        pushFreeCheckbox.checked = boolCheck(UM.Preferences.getValue("physics/automatic_push_free"))
        sendDataCheckbox.checked = boolCheck(UM.Preferences.getValue("info/send_slice_info"))
        scaleToFitCheckbox.checked = boolCheck(UM.Preferences.getValue("mesh/scale_to_fit"))
        languageComboBox.currentIndex = 0
    }

    GridLayout
    {
        columns: 2;
        //: Language selection label
        UM.I18nCatalog{id: catalog; name:"cura"}
        Label
        {
            id: languageLabel
            text: catalog.i18nc("@label","Language")
        }

        ComboBox
        {
            id: languageComboBox
            model: ListModel
            {
                id: languageList
                //: English language combo box option
                ListElement { text: QT_TR_NOOP("English"); code: "en" }
                //: German language combo box option
                ListElement { text: QT_TR_NOOP("German"); code: "de" }
                //: French language combo box option
    //            ListElement { text: QT_TR_NOOP("French"); code: "fr" }
                //: Spanish language combo box option
                ListElement { text: QT_TR_NOOP("Spanish"); code: "es" }
                //: Italian language combo box option
    //             ListElement { text: QT_TR_NOOP("Italian"); code: "it" }
                //: Finnish language combo box option
                ListElement { text: QT_TR_NOOP("Finnish"); code: "fi" }
                //: Russian language combo box option
                ListElement { text: QT_TR_NOOP("Russian"); code: "ru" }
            }

            currentIndex:
            {
                var code = UM.Preferences.getValue("general/language");
                for(var i = 0; i < languageList.count; ++i)
                {
                    if(model.get(i).code == code)
                    {
                        return i
                    }
                }
            }
            onActivated: UM.Preferences.setValue("general/language", model.get(index).code)

            anchors.left: languageLabel.right
            anchors.top: languageLabel.top
            anchors.leftMargin: 20

            Component.onCompleted:
            {
                // Because ListModel is stupid and does not allow using qsTr() for values.
                for(var i = 0; i < languageList.count; ++i)
                {
                    //languageList.setProperty(i, "text", catalog.i18nc("@action:menu",languageList.get(i).text));
                    languageList.setProperty(i, "text", languageList.get(i).text);
                }

                // Glorious hack time. ComboBox does not update the text properly after changing the
                // model. So change the indices around to force it to update.
                currentIndex += 1;
                currentIndex -= 1;
            }
        }

        Label
        {
            id: languageCaption;
            Layout.columnSpan: 2

            //: Language change warning
            text: catalog.i18nc("@label","You will need to restart the application for language changes to have effect.")
            wrapMode: Text.WordWrap
            font.italic: true
        }

        CheckBox
        {
            id: pushFreeCheckbox
            checked: boolCheck(UM.Preferences.getValue("physics/automatic_push_free"))
            onCheckedChanged: UM.Preferences.setValue("physics/automatic_push_free", checked)
        }
        Button
        {
            id: pushFreeText //is a button so the user doesn't have te click inconvenientley precise to enable or disable the checkbox

            //: Display Overhang preference checkbox
            text: catalog.i18nc("@option:check","Automatic push free");
            onClicked: pushFreeCheckbox.checked = !pushFreeCheckbox.checked

            //: Display Overhang preference tooltip
            tooltip: catalog.i18nc("@info:tooltip","Are objects on the platform automatically moved so they no longer intersect")

            style: ButtonStyle
            {
                background: Rectangle
                {
                    border.width: 0
                    color: "transparent"
                }
                label: Text
                {
                    renderType: Text.NativeRendering
                    horizontalAlignment: Text.AlignLeft
                    text: control.text
                }
            }
        }

        CheckBox
        {
            id: sendDataCheckbox
            checked: boolCheck(UM.Preferences.getValue("info/send_slice_info"))
            onCheckedChanged: UM.Preferences.setValue("info/send_slice_info", checked)
        }
        Button
        {
            id: sendDataText //is a button so the user doesn't have te click inconvenientley precise to enable or disable the checkbox

            //: Display Overhang preference checkbox
            text: catalog.i18nc("@option:check","Send (anonymous) slice info");
            onClicked: sendDataCheckbox.checked = !sendDataCheckbox.checked

            //: Display Overhang preference tooltip
            tooltip: catalog.i18nc("@info:tooltip","Should anonymous data about your slices be sent to Ultimaker. No models or IP's are sent / stored.")

            style: ButtonStyle
            {
                background: Rectangle
                {
                    border.width: 0
                    color: "transparent"
                }
                label: Text
                {
                    renderType: Text.NativeRendering
                    horizontalAlignment: Text.AlignLeft
                    text: control.text
                }
            }
        }
        CheckBox
        {
            id: scaleToFitCheckbox
            checked: boolCheck(UM.Preferences.getValue("mesh/scale_to_fit"))
            onCheckedChanged: UM.Preferences.setValue("mesh/scale_to_fit", checked)
        }
        Button
        {
            id: scaleToFitText //is a button so the user doesn't have te click inconvenientley precise to enable or disable the checkbox

            //: Display Overhang preference checkbox
            text: catalog.i18nc("@option:check","Scale loaded meshes when too large");
            onClicked: scaleToFitCheckbox.checked = !scaleToFitCheckbox.checked

            //: Display Overhang preference tooltip
            tooltip: catalog.i18nc("@info:tooltip","Should loaded meshes be scaled to the max build volume if they are too large.")

            style: ButtonStyle
            {
                background: Rectangle
                {
                    border.width: 0
                    color: "transparent"
                }
                label: Text
                {
                    renderType: Text.NativeRendering
                    horizontalAlignment: Text.AlignLeft
                    text: control.text
                }
            }
        }
        Item { Layout.fillHeight: true; Layout.columnSpan: 2 }
    }
}
