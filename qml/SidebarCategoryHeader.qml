import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

Button {
    id: base;

    Layout.preferredHeight: UM.Theme.sizes.section.height;
    Layout.preferredWidth: UM.Theme.sizes.section.width;

    style: UM.Theme.styles.sidebar_category;
}
