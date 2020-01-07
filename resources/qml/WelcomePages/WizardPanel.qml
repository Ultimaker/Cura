// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This item is a wizard panel that contains a progress bar at the top and a content area that's beneath the progress
// bar.
//
Item
{
    id: base

    clip: true

    property var currentItem: (model == null) ? null : model.getItem(model.currentPageIndex)
    property var model: null

    // Convenience properties
    property var progressValue: model == null ? 0 : model.currentProgress
    property string pageUrl: currentItem == null ? "" : currentItem.page_url

    property alias progressBarVisible: progressBar.visible
    property alias backgroundColor: panelBackground.color

    signal showNextPage()
    signal showPreviousPage()
    signal goToPage(string page_id)  // Go to a specific page by the given page_id.
    signal endWizard()

    // Call the corresponding functions in the model
    onShowNextPage: model.goToNextPage()
    onShowPreviousPage: model.goToPreviousPage()
    onGoToPage: model.goToPage(page_id)
    onEndWizard: model.atEnd()

    Rectangle  // Panel background
    {
        id: panelBackground
        anchors.fill: parent
        radius: UM.Theme.getSize("default_radius").width
        color: UM.Theme.getColor("main_background")

        UM.ProgressBar
        {
            id: progressBar
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right

            height: UM.Theme.getSize("progressbar").height

            value: base.progressValue
        }

        Loader
        {
            id: contentLoader
            anchors
            {
                margins: UM.Theme.getSize("wide_margin").width
                bottomMargin: UM.Theme.getSize("default_margin").width
                top: progressBar.bottom
                bottom: parent.bottom
                left: parent.left
                right: parent.right
            }
            source: base.pageUrl
            enabled: base.visible
        }
    }
}
