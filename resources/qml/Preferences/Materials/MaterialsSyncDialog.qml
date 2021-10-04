//Copyright (c) 2021 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 2.1
import QtQuick.Window 2.1
import UM 1.2 as UM

Window
{
    id: materialsSyncDialog
    property variant catalog: UM.I18nCatalog { name: "cura" }

    title: catalog.i18nc("@title:window", "Sync materials with printers")
    minimumWidth: UM.Theme.getSize("modal_window_minimum").width
    minimumHeight: UM.Theme.getSize("modal_window_minimum").height
    width: minimumWidth
    height: minimumHeight
    modality: Qt.ApplicationModal

    SwipeView
    {
        id: swipeView
        anchors.fill: parent

        Rectangle
        {
            id: introPage
            color: UM.Theme.getColor("main_background")
            Column
            {
                spacing: UM.Theme.getSize("default_margin").height
                anchors.fill: parent
                anchors.margins: UM.Theme.getSize("default_margin").width

                Label
                {
                    text: catalog.i18nc("@title:header", "Sync materials with printers")
                    font: UM.Theme.getFont("large_bold")
                    color: UM.Theme.getColor("text")
                }
                Label
                {
                    text: catalog.i18nc("@text", "Following a few simple steps, you will be able to synchronize all your material profiles with your printers.")
                    font: UM.Theme.getFont("medium")
                    color: UM.Theme.getColor("text")
                }
                Row
                {
                    /*
                    This is a row with 3 images, and a dashed line between each of them.
                    The images have various sizes, scaled to the window size:
                    - The computer screen and 3D printer have 1/3rd of the window size each.
                    - The remaining space is 2/3rds filled with the material spool image (so 2/9th in total).
                    - The remaining remaining space is divided equally over the two dashed lines (so 1/9th in total, or 1/18th per line).
                    */
                    width: parent.width
                    height: parent.height * 2 / 3
                    Item
                    {
                        width: Math.round(parent.width * 2 / 9)
                        height: parent.height
                        Image
                        {
                            id: spool_image
                            source: UM.Theme.getImage("material_spool")
                            width: parent.width - UM.Theme.getSize("default_margin").width
                            anchors.bottom: parent.bottom
                            fillMode: Image.PreserveAspectFit
                            sourceSize.width: width
                        }
                    }
                    Canvas
                    {
                        width: Math.round(parent.width / 18)
                        height: UM.Theme.getSize("thick_lining").width
                        onPaint: {
                            var ctx = getContext("2d");
                            ctx.setLineDash([2, 2]);
                            ctx.lineWidth = UM.Theme.getSize("thick_lining").width;
                            ctx.beginPath();
                            ctx.moveTo(0, height / 2);
                            ctx.lineTo(width, height / 2);
                            ctx.stroke();
                        }
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: spool_image.paintedHeight / 2 - height / 2 //Align to the vertical center of spool_image's real size.
                    }
                    Image
                    {
                        source: UM.Theme.getImage("connected_cura")
                        width: Math.round(parent.width / 3)
                        anchors.bottom: parent.bottom
                        fillMode: Image.PreserveAspectFit
                        sourceSize.width: width
                    }
                    Canvas
                    {
                        width: Math.round(parent.width / 18)
                        height: UM.Theme.getSize("thick_lining").width
                        onPaint: {
                            var ctx = getContext("2d");
                            ctx.setLineDash([2, 2]);
                            ctx.lineWidth = UM.Theme.getSize("thick_lining").width;
                            ctx.beginPath();
                            ctx.moveTo(0, height / 2);
                            ctx.lineTo(width, height / 2);
                            ctx.stroke();
                        }
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: spool_image.paintedHeight / 2 - height / 2 //Align to the vertical center of spool_image's real size.
                    }
                    Image
                    {
                        source: UM.Theme.getImage("3d_printer")
                        width: Math.round(parent.width / 3)
                        anchors.bottom: parent.bottom
                        fillMode: Image.PreserveAspectFit
                        sourceSize.width: width
                    }
                }
            }
        }
    }
}