// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Controls 2.4
import QtQuick.Layouts 1.3
import UM 1.5 as UM
import Cura 1.5 as Cura

UM.Dialog
{
    id: overrideConfirmationDialog

    property var printer: null

    minimumWidth: screenScaleFactor * 640;
    minimumHeight: screenScaleFactor * 320;
    width: minimumWidth
    height: minimumHeight
    title: catalog.i18nc("@title:window", "Configuration Changes")
    buttonSpacing: UM.Theme.getSize("narrow_margin").width
    rightButtons:
    [
        Cura.TertiaryButton
        {
            id: cancelButton
            text: catalog.i18nc("@action:button", "Cancel")
            onClicked:
            {
                overrideConfirmationDialog.reject()
            }
        },
        Cura.PrimaryButton
        {
            id: overrideButton
            text: catalog.i18nc("@action:button", "Override")
            onClicked:
            {
                OutputDevice.forceSendJob(printer.activePrintJob.key)
                overrideConfirmationDialog.close()
            }
            visible:
            {
                // Don't show the button if we're missing a printer or print job
                if (!printer || !printer.activePrintJob)
                {
                    return false
                }

                // Check each required change...
                for (var i = 0; i < printer.activePrintJob.configurationChanges.length; i++)
                {
                    var change = printer.activePrintJob.configurationChanges[i]
                    // If that type of change is in the list of blocking changes, hide the button
                    if (!change.canOverride)
                    {
                        return false
                    }
                }
                return true
            }
        }
    ]

    UM.Label
    {
        anchors
        {
            fill: parent
            margins: 36 * screenScaleFactor // TODO: Theme!
            bottomMargin: 56 * screenScaleFactor // TODO: Theme!
        }
        wrapMode: Text.WordWrap
        text:
        {
            if (!printer || !printer.activePrintJob)
            {
                return ""
            }
            var topLine
            if (materialsAreKnown(printer.activePrintJob))
            {
                topLine = catalog.i18ncp("@label", "The assigned printer, %1, requires the following configuration change:", "The assigned printer, %1, requires the following configuration changes:", printer.activePrintJob.configurationChanges.length).arg(printer.name)
            }
            else
            {
                topLine = catalog.i18nc("@label", "The printer %1 is assigned, but the job contains an unknown material configuration.").arg(printer.name)
            }
            var result = "<p>" + topLine +"</p>\n\n"
            for (var i = 0; i < printer.activePrintJob.configurationChanges.length; i++)
            {
                var change = printer.activePrintJob.configurationChanges[i]
                var text
                switch (change.typeOfChange)
                {
                    case "material_change":
                        text = catalog.i18nc("@label", "Change material %1 from %2 to %3.").arg(change.index + 1).arg(change.originName).arg(change.targetName)
                        break
                    case "material_insert":
                        text = catalog.i18nc("@label", "Load %3 as material %1 (This cannot be overridden).").arg(change.index + 1).arg(change.targetName)
                        break
                    case "print_core_change":
                        text = catalog.i18nc("@label", "Change print core %1 from %2 to %3.").arg(change.index + 1).arg(change.originName).arg(change.targetName)
                        break
                    default:
                        text = "unknown"
                }
                result += "<p><b>" + text + "</b></p>\n\n"
            }
            var bottomLine = catalog.i18nc("@label", "Override will use the specified settings with the existing printer configuration. This may result in a failed print.")
            result += "<p>" + bottomLine + "</p>\n\n"
            return result
        }
    }
    // Utils
    function formatPrintJobName(name)
    {
        var extensions = [ ".gcode.gz", ".gz", ".gcode", ".ufp", ".makerbot" ]
        for (var i = 0; i < extensions.length; i++)
        {
            var extension = extensions[i]
            if (name.slice(-extension.length) === extension)
            {
                name = name.substring(0, name.length - extension.length)
            }
        }
        return name;
    }
    function materialsAreKnown(job)
    {
        var conf0 = job.configuration[0]
        if (conf0 && !conf0.material.material)
        {
            return false
        }
        var conf1 = job.configuration[1]
        if (conf1 && !conf1.material.material)
        {
            return false
        }
        return true
    }
}
