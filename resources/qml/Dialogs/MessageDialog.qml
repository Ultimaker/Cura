// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import UM 1.5 as UM
import Cura 1.5 as Cura

// Wrapper around the UM.MessageBox with the primary/secondarybuttons
// set to Cura.PrimaryButton and Cura.SecondaryButton respectively
UM.MessageDialog
{
    primaryButton: Cura.PrimaryButton
    {
        text: model.text
    }

    secondaryButton: Cura.TertiaryButton
    {
        text: model.text
    }
}