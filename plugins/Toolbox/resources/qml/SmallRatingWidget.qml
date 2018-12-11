import QtQuick 2.3
import QtQuick.Controls 1.4
import UM 1.1 as UM
import Cura 1.1 as Cura



Row
{
    id: rating
    height: UM.Theme.getSize("rating_star").height
    visible: model.average_rating > 0 //Has a rating at all.
    spacing: UM.Theme.getSize("thick_lining").width

    UM.RecolorImage
    {
        id: starIcon
        source: UM.Theme.getIcon("star_filled")
        color: model.user_rating == 0  ? "#5a5a5a" : UM.Theme.getColor("primary")
        height: UM.Theme.getSize("rating_star").height
        width: UM.Theme.getSize("rating_star").width
    }

    Label
    {
        text: model.average_rating.toFixed(1) + " (" + model.num_ratings + " " + catalog.i18nc("@label", "ratings") + ")"
        verticalAlignment: Text.AlignVCenter
        height: starIcon.height
        anchors.verticalCenter: starIcon.verticalCenter
        color: starIcon.color
        font: UM.Theme.getFont("small")
    }
}