import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Rectangle {
    Layout.preferredHeight: UM.Theme.sizes.section.height;
    Layout.preferredWidth: UM.Theme.sizes.section.width;

    color: UM.Theme.colors.primary;

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
}
