import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    implicitWidth: layout.implicitWidth + 16
    implicitHeight: layout.implicitHeight + 2
    Layout.fillWidth: true

    property bool header: false
    property string ingredientName: ""
    property var quantity: undefined
    property string unit: ""
    property var ppu: undefined
    property var total: undefined
    property var weight: undefined
    property bool showOverlays: false
    property string zoneType: ""

    readonly property color overlayColor: {
        if (!showOverlays) {
            return "transparent"
        }
        switch (zoneType) {
        case "bloco-ingredientes":
            return "#eef5ff"
        case "bloco-food-cost":
            return "#fff5e8"
        default:
            return "#f3f6fb"
        }
    }

    Rectangle {
        id: backgroundRect
        anchors.fill: parent
        radius: header ? 6 : 4
        color: header ? Qt.rgba(200 / 255, 200 / 255, 200 / 255, 0.5) : overlayColor
        border.width: header ? 1 : (showOverlays ? 1 : 0)
        border.color: header ? Qt.rgba(0, 0, 0, 0.3) : (showOverlays ? "#4a6fa5" : "transparent")
        antialiasing: header

        Rectangle {
            visible: header
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            height: 1
            radius: parent.radius
            color: Qt.rgba(1, 1, 1, 0.8)
            antialiasing: true
            z: 1
        }

        Rectangle {
            visible: header
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            width: 1
            radius: parent.radius
            color: Qt.rgba(1, 1, 1, 0.8)
            antialiasing: true
            z: 1
        }

        Rectangle {
            visible: header
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 1
            radius: parent.radius
            color: Qt.rgba(0, 0, 0, 0.4)
            antialiasing: true
            z: 2
        }

        Rectangle {
            visible: header
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            width: 1
            radius: parent.radius
            color: Qt.rgba(0, 0, 0, 0.4)
            antialiasing: true
            z: 2
        }
    }

    RowLayout {
        id: layout
        anchors.fill: parent
        anchors.margins: 2
        spacing: 12

        Label {
            id: nameLabel
            text: header ? String(ingredientName).toUpperCase() : (ingredientName || "—")
            font.bold: header
            color: header ? "#2c3e66" : "#172b4d"
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            horizontalAlignment: header ? Text.AlignHCenter : Text.AlignLeft
            verticalAlignment: Text.AlignVCenter
        }

        Label {
            id: quantityLabel
            text: header ? String(quantity).toUpperCase() : root.formatNumber(quantity, 3)
            font.bold: header
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
            Layout.preferredWidth: 96
            color: header ? "#2c3e66" : "#42526e"
        }

        Label {
            id: unitLabel
            text: header ? String(unit).toUpperCase() : (unit || "—")
            font.bold: header
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            Layout.preferredWidth: 72
            color: header ? "#2c3e66" : "#42526e"
        }

        Label {
            id: ppuLabel
            text: header ? String(ppu).toUpperCase() : root.formatCurrency(ppu)
            font.bold: header
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
            Layout.preferredWidth: 100
            color: header ? "#2c3e66" : "#42526e"
        }

        Label {
            id: totalLabel
            text: header ? String(total).toUpperCase() : root.formatCurrency(total)
            font.bold: header
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
            Layout.preferredWidth: 110
            color: header ? "#2c3e66" : "#42526e"
        }

        Label {
            id: weightLabel
            text: header ? String(weight).toUpperCase() : root.formatNumber(weight, 3)
            font.bold: header
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            Layout.preferredWidth: 100
            Layout.minimumWidth: 100
            Layout.maximumWidth: 100
            color: header ? "#2c3e66" : "#42526e"
        }
    }

    function formatNumber(value, decimals) {
        if (value === undefined || value === null || value === "") {
            return "";
        }
        var number = Number(value);
        if (isNaN(number)) {
            return value;
        }
        return Qt.locale().toString(number, "f", decimals);
    }

    function formatCurrency(value) {
        if (value === undefined || value === null || value === "") {
            return "";
        }
        var number = Number(value);
        if (isNaN(number)) {
            return value;
        }
        return Qt.locale().toCurrencyString(number, "EUR");
    }
}
