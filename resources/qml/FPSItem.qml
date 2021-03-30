import QtQuick 2.0
import QtQuick.Window 2.2
import UM 1.3 as UM

// This is an QML item that shows the FPS and a running average of the FPS.
Item
{
    id: base
    property alias backgroundColor: background.color
    property alias textColor: fpsText.color

    property int numMeasurementsToAverage: 3

    width:  fpsText.contentWidth + UM.Theme.getSize("default_margin").height
    height: fpsText.contentHeight + UM.Theme.getSize("default_margin").height

    Rectangle
    {
        id: background

        // We use a trick here to figure out how often we can get a redraw triggered.
        // By adding a rotating rectangle, we can increase a counter by one every time we get notified.
        // After that, we trigger a timer once every second to look at that number.
        property int frameCounter: 0
        property int averageFrameCounter: 0
        property int counter: 0
        property int fps: 0
        property real averageFps: 0.0

        color: UM.Theme.getColor("primary")

        width: parent.width
        height: parent.height

        Rectangle
        {
            width: 0
            height: 0
            NumberAnimation on rotation
            {
                from: 0
                to: 360
                duration: 1000
                loops: Animation.Infinite
            }
            onRotationChanged: parent.frameCounter++;
            visible: false
        }

        Text
        {
            id: fpsText
            anchors.fill:parent
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("default")
            text: "Ø " + parent.averageFps + " | " + parent.fps + " fps"
        }

        Timer
        {
            interval: 1000
            repeat: true
            running: true
            onTriggered:
            {
                parent.averageFrameCounter += parent.frameCounter;
                parent.fps = parent.frameCounter;
                parent.counter++;
                parent.frameCounter = 0;
                if (parent.counter >= base.numMeasurementsToAverage)
                {
                    parent.averageFps = (parent.averageFrameCounter / parent.counter).toFixed(2)
                    parent.averageFrameCounter = 0;
                    parent.counter = 0;
                }
            }
        }
    }
}