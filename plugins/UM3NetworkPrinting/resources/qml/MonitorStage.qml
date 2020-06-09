// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.
import QtQuick 2.2
import QtWebEngine 1.4

Component
{
    WebEngineView
    {
        id: webEngine
        anchors.fill: parent
        url: "https://digitalfactory.ultimaker.com/app/jobs/" + OutputDevice.key // visit the correct page automatically
        userScripts: [
            WebEngineScript {
                injectionPoint: WebEngineScript.DocumentCreation
                sourceUrl: Qt.resolvedUrl("modifications.js")
                worldId: WebEngineScript.MainWorld
            }
	    ]
    }
}
