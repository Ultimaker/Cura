// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

StackView
{
    id: sidebarContents

    delegate: StackViewDelegate
    {
        function transitionFinished(properties)
        {
            properties.exitItem.opacity = 1
        }

        pushTransition: StackViewTransition
        {
            PropertyAnimation
            {
                target: enterItem
                property: "opacity"
                from: 0
                to: 1
                duration: 100
            }
            PropertyAnimation
            {
                target: exitItem
                property: "opacity"
                from: 1
                to: 0
                duration: 100
            }
        }
    }
}