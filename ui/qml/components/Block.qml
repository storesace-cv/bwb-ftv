import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    implicitWidth: blockBackground.implicitWidth
    implicitHeight: blockBackground.implicitHeight

    property string title: ""
    property var product: ({})
    property bool showOverlays: false
    default property alias content: zoneContainer.children

    Rectangle {
        id: blockBackground
        anchors.fill: parent
        radius: 16
        color: "#ffffff"
        border.color: "#d0d7e3"
        border.width: 1
    }

    ColumnLayout {
        id: blockLayout
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        Label {
            id: titleLabel
            objectName: root.objectName + "_title"
            text: root.title
            font.pixelSize: 20
            font.bold: true
            color: "#253858"
            Layout.fillWidth: true
            visible: text.length > 0
        }

        ColumnLayout {
            id: zoneContainer
            Layout.fillWidth: true
            spacing: 12
        }
    }
}
