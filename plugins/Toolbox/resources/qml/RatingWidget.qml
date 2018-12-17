import QtQuick 2.7
import QtQuick.Controls 2.1
import UM 1.0 as UM
import Cura 1.1 as Cura
Item
{
    id: ratingWidget

    property real rating: 0
    property int indexHovered: -1
    property string packageId: ""

    property int userRating: 0
    property bool canRate: false

    signal rated(int rating)

    width: contentRow.width
    height: contentRow.height
    MouseArea
    {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: ratingWidget.canRate
        acceptedButtons: Qt.NoButton
        onExited:
        {
            if(ratingWidget.canRate)
            {
                ratingWidget.indexHovered = -1
            }
        }

        Row
        {
            id: contentRow
            height: childrenRect.height
            Repeater
            {
                model: 5 // We need to get 5 stars
                Button
                {
                    id: control
                    hoverEnabled: true
                    onHoveredChanged:
                    {
                        if(hovered && ratingWidget.canRate)
                        {
                            indexHovered = index
                        }
                    }

                    ToolTip.visible: control.hovered  && !ratingWidget.canRate
                    ToolTip.text: !Cura.API.account.isLoggedIn ? catalog.i18nc("@label", "You need to login first before you can rate"): catalog.i18nc("@label", "You need to install the package before you can rate")

                    property bool isStarFilled:
                    {
                        // If the entire widget is hovered, override the actual rating.
                        if(ratingWidget.indexHovered >= 0)
                        {
                            return indexHovered >= index
                        }

                        if(ratingWidget.userRating > 0)
                        {
                            return userRating >= index +1
                        }

                        return rating >= index + 1
                    }

                    contentItem: Item {}
                    height: UM.Theme.getSize("rating_star").height
                    width: UM.Theme.getSize("rating_star").width
                    background: UM.RecolorImage
                    {
                        source: UM.Theme.getIcon(control.isStarFilled ? "star_filled" : "star_empty")
                        sourceSize.width: width
                        sourceSize.height: height

                        // Unfilled stars should always have the default color. Only filled stars should change on hover
                        color:
                        {
                            if(!ratingWidget.canRate)
                            {
                                return UM.Theme.getColor("rating_star")
                            }
                            if((ratingWidget.indexHovered >= 0 || ratingWidget.userRating > 0) && isStarFilled)
                            {
                                return UM.Theme.getColor("primary")
                            }
                            return UM.Theme.getColor("rating_star")
                        }
                    }
                    onClicked:
                    {
                        if(ratingWidget.canRate)
                        {
                            rated(index + 1)  // Notify anyone who cares about this.
                        }
                    }
                }
            }
        }
    }
}