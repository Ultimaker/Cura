import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.4
import UM 1.3 as UM


Rectangle {
    id: menuBackground;

    property QtObject window;
    Binding {
        target: menu.__contentItem
        property: "width"
        value: window.width
        when: !menu.__isNative
    }

    default property alias menus: menu.menus

    property alias estilo: menu.style

    width: menu.__isNative ? 0 : menu.__contentItem.width
    height: menu.__isNative ? 0 : menu.__contentItem.height

    color: palette.window;

    Keys.forwardTo: menu.__contentItem;

    property color menuBackgroundColor: UM.Theme.getColor("primary_button_text")
    property color menuForeColor: UM.Theme.getColor("secondary_button_hover")
    property color menuTextColor: UM.Theme.getColor("viewport_overlay")
    
    MenuBar
    {
        id: menu

        Component.onCompleted:
        {
            __contentItem.parent = menuBackground;
        }
        style: MenuBarStyle {
            background: Rectangle {
                id: rect
                color: menuBackgroundColor
            }

            itemDelegate: Rectangle {
                implicitWidth: lab.contentWidth + 20   
                implicitHeight: lab.contentHeight      
                color: styleData.selected || styleData.open ? menuForeColor : menuBackgroundColor
                Label {
                    id: lab
                    text: formatMnemonic(styleData.text, true) 
                    font: UM.Theme.getFont("large")
                    color: menuTextColor
                    leftPadding: 10
                }
            }

            menuStyle: MenuStyle {
                id: menuStyle
                frame: Rectangle {
                    color: menuBackgroundColor
                }
                itemDelegate {
                    background: Rectangle {
                        color:  styleData.selected || styleData.open ? menuForeColor : menuBackgroundColor
                        radius: styleData.selected ? 3 : 0
                    }
                    label: Label {
                        text: formatMnemonic(styleData.text, true) 
                        font: UM.Theme.getFont("large")
                        color: menuTextColor
                    }
                    shortcut: Label {
                        text: styleData.shortcut
                        color: menuTextColor
                    }
                }
            }
        }
    }

    SystemPalette {
        id: palette
        colorGroup: SystemPalette.Active
    }
}
