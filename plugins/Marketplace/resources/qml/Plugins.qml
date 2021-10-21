// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import Cura 1.7 as Cura

Item
{
    Repeater
    {
        model: Cura.PackageList{}

        Label
        {
            text: "Test"  //TODO: Create a card for each package.
        }
    }
}