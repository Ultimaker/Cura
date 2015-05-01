import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1

import UM 1.0 as UM

Rectangle {
    id: base

    opacity: 0;

    width: 300;
    height: label.height + label.anchors.topMargin + label.anchors.bottomMargin;

    border.width: 1;

    Label {
        id: label;

        wrapMode: Text.WordWrap;
        horizontalAlignment: Text.AlignJustify;

        anchors.left: parent.left;
        anchors.leftMargin: 10;
        anchors.right: parent.right;
        anchors.rightMargin: 10;
        anchors.top: parent.top;
        anchors.topMargin: closeButton.height;
        anchors.bottomMargin: 10;
    }

    ToolButton {
        id: closeButton;
        anchors.right: parent.right;
        text: "Close";
        onClicked: closeAnimation.start();
    }

    function show(text, x, y)
    {
        if(base.opacity > 0) {
            base._newText = text;
            base._newY = y;
            textChangeAnimation.start();
        } else {
            label.text = text;
            base.y = y;
            showAnimation.start();
        }
    }

    property string _newText;
    property real _newY;

    SequentialAnimation {
        id: textChangeAnimation;

        NumberAnimation { target: base; property: "opacity"; to: 0; duration: 100; }
        PropertyAction { target: label; property: "text"; value: base._newText; }
        PropertyAction { target: base; property: "y"; value: base._newY; }
        NumberAnimation { target: base; property: "opacity"; to: 1; duration: 100; }
    }

    NumberAnimation { id: showAnimation; target: base; property: "opacity"; to: 1; duration: 100; }
    NumberAnimation { id: closeAnimation; target: base; property: "opacity"; to: 0; duration: 100; }
}
