// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM

UM.Dialog
{
    width: minimumWidth;
    minimumWidth: 350 * screenScaleFactor;

    height: minimumHeight;
    minimumHeight: 250 * screenScaleFactor;

    title: catalog.i18nc("@title:window", "Convert Image...")

    GridLayout
    {
        UM.I18nCatalog{id: catalog; name: "cura"}
        anchors.fill: parent;
        Layout.fillWidth: true
        columnSpacing: 16 * screenScaleFactor
        rowSpacing: 4 * screenScaleFactor
        columns: 1

        UM.TooltipArea {
            Layout.fillWidth:true
            height: childrenRect.height
            text: catalog.i18nc("@info:tooltip","The maximum distance of each pixel from \"Base.\"")
            Row {
                width: parent.width

                Label {
                    text: catalog.i18nc("@action:label", "Height (mm)")
                    width: 150 * screenScaleFactor
                    anchors.verticalCenter: parent.verticalCenter
                }

                TextField {
                    id: peak_height
                    objectName: "Peak_Height"
                    validator: RegExpValidator {regExp: /^-?\d{1,3}([\,|\.]\d*)?$/}
                    width: 180 * screenScaleFactor
                    onTextChanged: { manager.onPeakHeightChanged(text) }
                }
            }
        }

        UM.TooltipArea {
            Layout.fillWidth:true
            height: childrenRect.height
            text: catalog.i18nc("@info:tooltip","The base height from the build plate in millimeters.")
            Row {
                width: parent.width

                Label {
                    text: catalog.i18nc("@action:label", "Base (mm)")
                    width: 150 * screenScaleFactor
                    anchors.verticalCenter: parent.verticalCenter
                }

                TextField {
                    id: base_height
                    objectName: "Base_Height"
                    validator: RegExpValidator {regExp: /^\d{1,3}([\,|\.]\d*)?$/}
                    width: 180 * screenScaleFactor
                    onTextChanged: { manager.onBaseHeightChanged(text) }
                }
            }
        }

        UM.TooltipArea {
            Layout.fillWidth:true
            height: childrenRect.height
            text: catalog.i18nc("@info:tooltip","The width in millimeters on the build plate.")
            Row {
                width: parent.width

                Label {
                    text: catalog.i18nc("@action:label", "Width (mm)")
                    width: 150 * screenScaleFactor
                    anchors.verticalCenter: parent.verticalCenter
                }

                TextField {
                    id: width
                    objectName: "Width"
                    focus: true
                    validator: RegExpValidator {regExp: /^[1-9]\d{0,2}([\,|\.]\d*)?$/}
                    width: 180 * screenScaleFactor
                    onTextChanged: { manager.onWidthChanged(text) }
                }
            }
        }

        UM.TooltipArea {
            Layout.fillWidth:true
            height: childrenRect.height
            text: catalog.i18nc("@info:tooltip","The depth in millimeters on the build plate")
            Row {
                width: parent.width

                Label {
                    text: catalog.i18nc("@action:label", "Depth (mm)")
                    width: 150 * screenScaleFactor
                    anchors.verticalCenter: parent.verticalCenter
                }
                TextField {
                    id: depth
                    objectName: "Depth"
                    focus: true
                    validator: RegExpValidator {regExp: /^[1-9]\d{0,2}([\,|\.]\d*)?$/}
                    width: 180 * screenScaleFactor
                    onTextChanged: { manager.onDepthChanged(text) }
                }
            }
        }

        UM.TooltipArea {
            Layout.fillWidth:true
            height: childrenRect.height
            text: catalog.i18nc("@info:tooltip","By default, white pixels represent high points on the mesh and black pixels represent low points on the mesh. Change this option to reverse the behavior such that black pixels represent high points on the mesh and white pixels represent low points on the mesh.")
            Row {
                width: parent.width

                //Empty label so 2 column layout works.
                Label {
                    text: ""
                    width: 150 * screenScaleFactor
                    anchors.verticalCenter: parent.verticalCenter
                }
                ComboBox {
                    id: image_color_invert
                    objectName: "Image_Color_Invert"
                    model: [ catalog.i18nc("@item:inlistbox","Lighter is higher"), catalog.i18nc("@item:inlistbox","Darker is higher") ]
                    width: 180 * screenScaleFactor
                    onCurrentIndexChanged: { manager.onImageColorInvertChanged(currentIndex) }
                }
            }
        }

        UM.TooltipArea {
            Layout.fillWidth:true
            height: childrenRect.height
            text: catalog.i18nc("@info:tooltip","The amount of smoothing to apply to the image.")
            Row {
                width: parent.width

                Label {
                    text: catalog.i18nc("@action:label", "Smoothing")
                    width: 150 * screenScaleFactor
                    anchors.verticalCenter: parent.verticalCenter
                }

                Item {
                    width: 180 * screenScaleFactor
                    height: 20 * screenScaleFactor
                    Layout.fillWidth: true

                    Slider {
                        id: smoothing
                        objectName: "Smoothing"
                        maximumValue: 100.0
                        stepSize: 1.0
                        width: 180
                        onValueChanged: { manager.onSmoothingChanged(value) }
                    }
                }
            }
        }
    }

    rightButtons: [
        Button
        {
            id:ok_button
            text: catalog.i18nc("@action:button","OK");
            onClicked: { manager.onOkButtonClicked() }
            enabled: true
        },
        Button
        {
            id:cancel_button
            text: catalog.i18nc("@action:button","Cancel");
            onClicked: { manager.onCancelButtonClicked() }
            enabled: true
        }
    ]
}
