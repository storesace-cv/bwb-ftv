import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    implicitWidth: layout.implicitWidth + 16
    implicitHeight: layout.implicitHeight + 4
    Layout.fillWidth: true

    property bool header: false
    property string ingredientName: ""
    property var quantity: undefined
    property string unit: ""
    property var ppu: undefined
    property var total: undefined
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
        anchors.fill: parent
        radius: header ? 6 : 4
        color: header ? "#e9edf5" : overlayColor
        border.width: header ? 0 : (showOverlays ? 1 : 0)
        border.color: showOverlays ? "#4a6fa5" : "transparent"
    }

    RowLayout {
        id: layout
        anchors.fill: parent
        anchors.margins: 4
        spacing: 12

        Label {
            id: nameLabel
            text: header ? ingredientName : (ingredientName || "—")
            font.bold: header
            color: header ? "#2c3e66" : "#172b4d"
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
        }

        Label {
            id: quantityLabel
            text: header ? quantity : root.formatNumber(quantity, 3)
            font.bold: header
            horizontalAlignment: Text.AlignRight
            Layout.preferredWidth: 96
            color: header ? "#2c3e66" : "#42526e"
        }

        Label {
            id: unitLabel
            text: header ? unit : (unit || "—")
            font.bold: header
            horizontalAlignment: Text.AlignLeft
            Layout.preferredWidth: 72
            color: header ? "#2c3e66" : "#42526e"
        }

        Label {
            id: ppuLabel
            text: header ? ppu : root.formatCurrency(ppu)
            font.bold: header
            horizontalAlignment: Text.AlignRight
            Layout.preferredWidth: 100
            color: header ? "#2c3e66" : "#42526e"
        }

        Label {
            id: totalLabel
            text: header ? total : root.formatCurrency(total)
            font.bold: header
            horizontalAlignment: Text.AlignRight
            Layout.preferredWidth: 110
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
