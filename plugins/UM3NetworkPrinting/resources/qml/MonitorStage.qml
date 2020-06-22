// Copyright (c) 2020 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.
import QtQuick 2.2
import QtWebEngine 1.4

Component
{
    WebEngineView
    {
        id: webEngine
        anchors.fill: parent

        // visits the correct page automatically
        url: CuraApplication.ultimakerDigitalFactoryUrl + "/app/jobs/" + OutputDevice.key

        // inject a script to make some UI modifications
        userScripts: [
            WebEngineScript {
                injectionPoint: WebEngineScript.DocumentCreation
                sourceUrl: Qt.resolvedUrl("modifications.js")
                worldId: WebEngineScript.MainWorld
            }
	    ]

	    // this signal is triggered when the user click on an href in the HTML
	    // we open these in an actual browser to prevent getting stuck in this web view
	    onNewViewRequested: function(request) {
	        if (request.userInitiated) {
	            Qt.openUrlExternally(request.requestedUrl)
	        }
	    }
    }
}
