// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura

import "../Widgets"


Item
{
    id: base

    clip: true

    property int currentStep: 0
    property int totalStepCount: (model == null) ? 0 : model.count
    property real progressValue: (totalStepCount == 0) ? 0 : (currentStep / totalStepCount)

    property var currentItem: (model == null) ? null : model.getItem(currentStep)
    property var model: null

    signal showNextPage()
    signal showPreviousPage()
    signal passLastPage()  // Emitted when there is no more page to show
    signal goToPage(string page_id)  // Go to a specific page by the given page_id.

    onShowNextPage:
    {
        if (currentStep < totalStepCount - 1)
        {
            currentStep++
        }
        else
        {
            passLastPage()
        }
    }

    onShowPreviousPage:
    {
        if (currentStep > 0)
        {
            currentStep--
        }
    }

    onGoToPage:
    {
        // find the page index
        var page_index = -1
        for (var i = 0; i < base.model.count; i++)
        {
            const item = base.model.getItem(i)
            if (item.id == page_id)
            {
                page_index = i
                break
            }
        }
        if (page_index > 0)
        {
            currentStep = page_index
        }
    }

    onVisibleChanged:
    {
        if (visible)
        {
            base.currentStep = 0
            base.currentItem = base.model.getItem(base.currentStep)
        }
    }

    onModelChanged:
    {
        base.currentStep = 0
    }

    Rectangle  // Panel background
    {
        id: panelBackground
        anchors.fill: parent
        radius: UM.Theme.getSize("default_radius").width

        CuraProgressBar
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
                margins: base.contentMargins
                top: progressBar.bottom
                bottom: parent.bottom
                left: parent.left
                right: parent.right
            }
            source: base.currentItem.page_url
        }
    }
}
