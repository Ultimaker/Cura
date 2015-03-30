import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

UM.AngledCornerRectangle {
    id: base;

    Layout.preferredHeight: UM.Theme.sizes.section.height;
    Layout.preferredWidth: UM.Theme.sizes.section.width;

    property bool clickable: false;
    signal clicked();

    color: clickable ? UM.Theme.colors.button : UM.Theme.colors.primary;
    cornerSize: UM.Theme.sizes.default_margin.width;

    property alias icon: iconImage.source;
    property alias text: label.text;

    Image {
        id: iconImage;
        anchors {
            left: parent.left;
            leftMargin: UM.Theme.sizes.default_margin.width;
            verticalCenter: parent.verticalCenter;
        }

        width: UM.Theme.sizes.section_icon.width;
        height: UM.Theme.sizes.section_icon.width;

        sourceSize.width: width;
        sourceSize.height: height;
    }

    Label {
        id: label

        anchors {
            left: iconImage.right;
            leftMargin: UM.Theme.sizes.default_margin.width;
            right: parent.right;
            rightMargin: UM.Theme.sizes.default_margin.width;
            verticalCenter: parent.verticalCenter;
        }

        font: UM.Theme.fonts.large;
        color: UM.Theme.colors.primary_text;
    }

    MouseArea {
        id: mouse;
        anchors.fill: parent;

        enabled: base.clickable;
        hoverEnabled: true;

        onClicked: {console.log('click'); base.clicked(); }
    }

    states: [
        State {
            name: "hover";
            when: mouse.containsMouse;

            PropertyChanges { target: base; color: UM.Theme.colors.button_hover; }
        },
        State {
            name: "down";
            when: mouse.pressed;

            PropertyChanges { target: base; color: UM.Theme.colors.button_down; }
        }
    ]
}
