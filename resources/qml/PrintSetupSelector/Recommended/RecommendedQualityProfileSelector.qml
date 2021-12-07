// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.12
import QtQuick.Controls 1.4
import QtQuick.Controls 2.3 as Controls2
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.15


import UM 1.2 as UM
import Cura 1.6 as Cura
import ".."

Item
{
    id: qualityRow
    height: childrenRect.height

    property real labelColumnWidth: Math.round(width / 3)
    property real settingsColumnWidth: width - labelColumnWidth

    // Here are the elements that are shown in the left column

    Column
    {

    spacing: UM.Theme.getSize("default_margin").height

        anchors{
            left: parent.left
            right: parent.right
        }


            Label
            {
                text: catalog.i18nc("@label", "Profiles")
                font: UM.Theme.getFont("medium")
            }

            Controls2.TabBar 
            {
                id: intentSelection
                width: parent.width
                height: UM.Theme.getSize("recomended_quality_tab").height
                spacing: UM.Theme.getSize("narrow_margin").width

                
                Repeater
                {

                model: Cura.IntentCategoryModel{}
                Controls2.TabButton{
                    id: "intentCategoryButton"
                    anchors.verticalCenter:parent.verticalCenter
                    height: parent.height
                    background: Rectangle{
                    color: (intentSelection.currentIndex==index) ? UM.Theme.getColor("setting_category_hover") : UM.Theme.getColor("main_background")
                    }
                    // function getFirstAvailableQuality(qualities){
                    //     console.log(qualities)

                    //     for(var i=0;i<qualities.count;i++){
                    //         console.log(qualities.name)
                    //         console.log(qualities.intent_category)

                    //         console.log(i, qualities.get(i).available)
                    //         if (qualities.available){
                    //             return i
                    //         }
                    //     }
                    // }
                    onClicked: Cura.IntentManager.selectIntent(model.intent_category, "normal" )
                    //onClicked: getFirstAvailableQuality(model["qualities"]")
                    
                         ColumnLayout{
                            spacing: 2
                            anchors.fill: parent
                            UM.RecolorImage
                            {
                                Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
                                id: intent_category
                                source: {      
                                    switch (model.name) {
                                        case "Default":
                                            UM.Theme.getIcon("Placeholder", "high")
                                            break
                                        case "Visual":
                                            UM.Theme.getIcon("Art", "high")
                                            break
                                        case "Engineering":
                                            UM.Theme.getIcon("Machine", "high")
                                            break
                                        case "Draft":
                                            UM.Theme.getIcon("Easy", "high")
                                            break
                                        default:
                                            UM.Theme.getIcon("Placeholder", "high")
                                            break    
                                    }
                                }
                                height: UM.Theme.getSize("high_resolution_icon").width/2
                                width: UM.Theme.getSize("high_resolution_icon").height/2
                                color: UM.Theme.getColor("text")
                            }
                            Text{ 
                                text: model.name
                                horizontalAlignment: Text.AlignHCenter
                                Layout.fillWidth:true
                                color: UM.Theme.getColor("text")
                        
                            }
                             
                        }
                        MouseArea // Intent description tooltip hover area
                        {
                            id: intentDescriptionHoverArea
                            anchors.fill: parent
                            hoverEnabled: true
                            enabled: model.description !== undefined
                            acceptedButtons: Qt.NoButton // react to hover only, don't steal clicks

                            Timer
                            {
                                id: intentTooltipTimer
                                interval: 500
                                running: false
                                repeat: false
                                onTriggered: base.showTooltip(
                                    intentCategoryButton,
                                    Qt.point(0, 0),
                                    model.description
                                )
                            }

                            onEntered: intentTooltipTimer.start()
                            onExited:
                            {
                                base.hideTooltip()
                                intentTooltipTimer.stop()
                            }
                        }
                    
                    } 
                }
                
            }

             StackLayout{
                width: parent.width
                currentIndex:intentSelection.currentIndex
                height:200
                
                Repeater
                {

                    model: Cura.IntentCategoryModel{}
                    
                    Column{
                        spacing:UM.Theme.getSize("default_margin").height
                
                        // Cura.IconWithText
                        // {
                        //     source: UM.Theme.getIcon("PrintQuality")
                        //     text: "resolution"
                        //     font: UM.Theme.getFont("default")
                        //     width: labelColumnWidth
                        //     iconSize: UM.Theme.getSize("medium_button_icon").width
                        // }

                        Label
                        {
                                text: catalog.i18nc("@label", "Resolution")
                                font: UM.Theme.getFont("default")

                        }

                        RowLayout
                        {
                            //width:parent.width
                            anchors.left:parent.left
                            anchors.right:parent.right
                            height: UM.Theme.getSize("recomended_resolution_button").height

                            spacing: UM.Theme.getSize("narrow_margin").width
                            property var intentCategory: model.intent_category
                            property var intentModel: model["qualities"]

                            Repeater
                            {
                                model: parent.intentModel
                                
                                Controls2.Button{
                                    property var intentCategoryLabel: parent.intentModel

                                    visible: model.available
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true

                                    checkable:true
                                    height: UM.Theme.getSize("recomended_resolution_button").height
                                    Layout.minimumWidth: UM.Theme.getSize("recomended_resolution_button").width

                                    background: Rectangle{
                                        anchors.fill:parent
                                        color: parent.checked ? UM.Theme.getColor("setting_category_hover") : UM.Theme.getColor("main_background")
                                    }
                                    
                                    property var modelData: {
                                        "intent_category": parent.intentCategory,
                                        "quality_type": model.quality_type
                                    }

                                    function checkedFunction(modelItem)
                                    {
                                        if(Cura.MachineManager.hasCustomQuality)
                                        {
                                            // When user created profile is active, no quality tickbox should be active.
                                            return false
                                        }

                                        if(modelItem === null)
                                        {
                                            return false
                                        }
                                        return Cura.MachineManager.activeQualityType == modelItem.quality_type && Cura.MachineManager.activeIntentCategory == modelItem.intent_category
                                    }

                                    checked: checkedFunction(modelData)


                                    Controls2.ButtonGroup.group: activeProfileButtonGroup
                                    
                                   
                                    Row{
                                        padding: UM.Theme.getSize("narrow_margin").width
                                        spacing: UM.Theme.getSize("narrow_margin").width

                                        UM.RecolorImage
                                            {
                                                id: buttonIconLeft
                                                source: {      
                                                        switch (model.layer_height) {
                                                            case 0.06:
                                                                UM.Theme.getIcon("ResolutionExtrafine", "high")
                                                                break
                                                            case 0.1:
                                                                UM.Theme.getIcon("ResolutionFine", "high")
                                                                break
                                                            case 0.15:
                                                                UM.Theme.getIcon("ResolutionNormal", "high")
                                                                break
                                                            case 0.2:
                                                                UM.Theme.getIcon("ResolutionFast", "high")
                                                                break
                                                            case 0.3:
                                                                UM.Theme.getIcon("ResolutionExtrFast", "high")
                                                                break
                                                            case 0.4:
                                                                UM.Theme.getIcon("ResolutionSprint", "high")
                                                                break
                                                            default:
                                                                UM.Theme.getIcon("ResolutionNormal", "high")
                                                                break    
                                                        }
                                                    }                                                
                                                height: UM.Theme.getSize("high_resolution_icon").width/2
                                                width: UM.Theme.getSize("high_resolution_icon").height/2
                                                color: UM.Theme.getColor("text")
                                            }
                                        Column{                                        
                                            Text{ text: model.name}
                                            Text{ text: model.layer_height}
                                        }
                                    }
                                }
                                                        
                            }



                        } 
                    }                    
                                
                }
            } 
         
        Controls2.ButtonGroup{
            id: activeProfileButtonGroup
            exclusive: true
            onClicked: Cura.IntentManager.selectIntent(button.modelData.intent_category, button.modelData.quality_type)
        }

       
        // Item
        // {
        //     height: childrenRect.height
        //     anchors
        //     {
        //         left: parent.left
        //         right: parent.right
        //     }
        //     Cura.IconWithText
        //     {
        //         id: profileLabel
        //         source: UM.Theme.getIcon("PrintQuality")
        //         text: catalog.i18nc("@label", "Profiles")
        //         font: UM.Theme.getFont("medium")
        //         width: labelColumnWidth
        //         iconSize: UM.Theme.getSize("medium_button_icon").width
        //     }
        //     UM.SimpleButton
        //     {
        //         id: resetToDefaultQualityButton

        //         visible: Cura.SimpleModeSettingsManager.isProfileCustomized || Cura.MachineManager.hasCustomQuality
        //         height: visible ? UM.Theme.getSize("print_setup_icon").height : 0
        //         width: height
        //         anchors
        //         {
        //             right: profileLabel.right
        //             rightMargin: UM.Theme.getSize("default_margin").width
        //             leftMargin: UM.Theme.getSize("default_margin").width
        //             verticalCenter: parent.verticalCenter
        //         }

        //         color: hovered ? UM.Theme.getColor("setting_control_button_hover") : UM.Theme.getColor("setting_control_button")
        //         iconSource: UM.Theme.getIcon("ArrowReset")

        //         onClicked:
        //         {
        //             // if the current profile is user-created, switch to a built-in quality
        //             Cura.MachineManager.resetToUseDefaultQuality()
        //         }
        //         onEntered:
        //         {
        //             var tooltipContent = catalog.i18nc("@tooltip","You have modified some profile settings. If you want to change these go to custom mode.")
        //             base.showTooltip(qualityRow, Qt.point(-UM.Theme.getSize("thick_margin").width, 0),  tooltipContent)
        //         }
        //         onExited: base.hideTooltip()
        //     }

        //     Cura.LabelBar
        //     {
        //         id: labelbar
        //         anchors
        //         {
        //             left: profileLabel.right
        //             right: parent.right
        //             verticalCenter: profileLabel.verticalCenter
        //         }

        //         model: Cura.QualityProfilesDropDownMenuModel
        //         modelKey: "layer_height"
        //     }
        // }



        // Repeater
        // {
        //     model: Cura.IntentCategoryModel {}
        //     Item
        //     {
        //         anchors
        //         {
        //             left: parent.left
        //             right: parent.right
        //         }
        //         height: intentCategoryLabel.height

        //         Label
        //         {
        //             id: intentCategoryLabel
        //             text: model.name
        //             width: labelColumnWidth - UM.Theme.getSize("section_icon").width
        //             anchors.left: parent.left
        //             anchors.leftMargin: UM.Theme.getSize("section_icon").width + UM.Theme.getSize("narrow_margin").width
        //             font: UM.Theme.getFont("medium")
        //             color: UM.Theme.getColor("text")
        //             renderType: Text.NativeRendering
        //             elide: Text.ElideRight
        //         }

        //         Cura.RadioCheckbar
        //         {
        //             anchors
        //             {
        //                 left: intentCategoryLabel.right
        //                 right: parent.right
        //             }
        //             dataModel: model["qualities"]
        //             buttonGroup: activeProfileButtonGroup

        //             function checkedFunction(modelItem)
        //             {
        //                 if(Cura.MachineManager.hasCustomQuality)
        //                 {
        //                     // When user created profile is active, no quality tickbox should be active.
        //                     return false
        //                 }

        //                 if(modelItem === null)
        //                 {
        //                     return false
        //                 }
        //                 return Cura.MachineManager.activeQualityType == modelItem.quality_type && Cura.MachineManager.activeIntentCategory == modelItem.intent_category
        //             }

        //             isCheckedFunction: checkedFunction
        //         }

        //         MouseArea // Intent description tooltip hover area
        //         {
        //             id: intentDescriptionHoverArea
        //             anchors.fill: parent
        //             hoverEnabled: true
        //             enabled: model.description !== undefined
        //             acceptedButtons: Qt.NoButton // react to hover only, don't steal clicks

        //             Timer
        //             {
        //                 id: intentTooltipTimer
        //                 interval: 500
        //                 running: false
        //                 repeat: false
        //                 onTriggered: base.showTooltip(
        //                     intentCategoryLabel,
        //                     Qt.point(-(intentCategoryLabel.x - qualityRow.x) - UM.Theme.getSize("thick_margin").width, 0),
        //                     model.description
        //                 )
        //             }

        //             onEntered: intentTooltipTimer.start()
        //             onExited:
        //             {
        //                 base.hideTooltip()
        //                 intentTooltipTimer.stop()
        //             }
        //         }

        //         NoIntentIcon // This icon has hover priority over intentDescriptionHoverArea, so draw it above it.
        //         {
        //             affected_extruders: Cura.MachineManager.extruderPositionsWithNonActiveIntent
        //             intent_type: model.name
        //             anchors.right: intentCategoryLabel.right
        //             anchors.rightMargin: UM.Theme.getSize("narrow_margin").width
        //             width: intentCategoryLabel.height * 0.75
        //             anchors.verticalCenter: parent.verticalCenter
        //             height: width
        //             visible: Cura.MachineManager.activeIntentCategory == model.intent_category && affected_extruders.length
        //         }


        //     }

        // }
    }
}
