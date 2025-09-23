import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15
import "components"

ApplicationWindow {
    id: root
    visible: true
    width: 1180
    height: 860
    title: qsTr("Ficha Técnica (Qt Quick)")

    property var product: productModel ? productModel : ({})
    property bool showDevOverlays: overlayController ? overlayController.showOverlays : false
    property int productTotal: 0
    property int currentIndex: -1
    property bool hasPrevious: currentIndex > 0
    property bool hasNext: currentIndex >= 0 && currentIndex < productTotal - 1

    function refreshProductTotal() {
        if (productService && productService.total) {
            var totalValue = Number(productService.total())
            if (isNaN(totalValue)) {
                totalValue = 0
            }
            if (productTotal !== totalValue) {
                productTotal = totalValue
            }
            return totalValue
        }
        return productTotal
    }

    function loadProduct(index) {
        if (!productService) {
            return
        }

        var totalValue = refreshProductTotal()
        if (totalValue <= 0) {
            currentIndex = -1
            return
        }

        if (index < 0 || index >= totalValue) {
            return
        }

        var codigo = productService.codigo_at(index)
        if (!codigo) {
            return
        }

        var info = productService.get_product_info(codigo)
        if (info) {
            root.product = info
            currentIndex = index
        }
    }

    function loadPrevious() {
        if (hasPrevious) {
            loadProduct(currentIndex - 1)
        }
    }

    function loadNext() {
        if (hasNext) {
            loadProduct(currentIndex + 1)
        }
    }

    Component.onCompleted: {
        if (!productService) {
            productTotal = product ? 1 : 0
            currentIndex = productTotal > 0 ? 0 : -1
            return
        }

        var totalValue = refreshProductTotal()
        if (totalValue > 0) {
            loadProduct(0)
        }
    }

    background: Rectangle {
        color: "#f3f6fb"
    }

    Window {
        id: aboutWindow
        modality: Qt.WindowModal
        flags: Qt.Dialog
        width: 360
        height: 220
        title: qsTr("Sobre a aplicação")
        visible: false

        Rectangle {
            anchors.fill: parent
            color: "white"
            radius: 8

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 16

                Label {
                    text: qsTr("Ficha Técnica Viewer")
                    font.bold: true
                    Layout.fillWidth: true
                }

                Label {
                    text: qsTr("Visualização experimental das fichas técnicas.")
                    wrapMode: Text.Wrap
                    Layout.fillWidth: true
                }

                Item {
                    Layout.fillHeight: true
                }

                Button {
                    text: qsTr("Fechar")
                    Layout.alignment: Qt.AlignRight
                    onClicked: aboutWindow.close()
                }
            }
        }
    }

    menuBar: MenuBar {
        Menu {
            title: qsTr("Ficheiro")

            MenuItem {
                text: qsTr("Sobre…")
                onTriggered: aboutWindow.open()
            }

            MenuItem {
                text: qsTr("Fechar Sobre")
                enabled: aboutWindow.visible
                onTriggered: aboutWindow.close()
            }

            MenuSeparator {}

            MenuItem {
                text: qsTr("Sair")
                onTriggered: Qt.quit()
            }
        }

        Menu {
            title: qsTr("Navegação")

            MenuItem {
                text: qsTr("Anterior")
                enabled: root.hasPrevious
                onTriggered: root.loadPrevious()
            }

            MenuItem {
                text: qsTr("Seguinte")
                enabled: root.hasNext
                onTriggered: root.loadNext()
            }
        }
    }

    header: ToolBar {
        RowLayout {
            anchors.fill: parent
            anchors.margins: 8
            spacing: 12

            ToolButton {
                text: "\u25C0"
                enabled: root.hasPrevious
                onClicked: root.loadPrevious()
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Anterior")
            }

            Label {
                Layout.fillWidth: true
                text: root.product && root.product.code ? root.product.code + " — " + root.product.name : qsTr("Sem produto selecionado")
                elide: Text.ElideRight
            }

            ToolButton {
                text: "\u25B6"
                enabled: root.hasNext
                onClicked: root.loadNext()
                ToolTip.visible: hovered
                ToolTip.text: qsTr("Seguinte")
            }
        }
    }

    ColumnLayout {
        id: layoutRoot
        anchors.fill: parent
        anchors.margins: 24
        spacing: 24

        Block {
            id: identificationBlock
            objectName: "block_identificacao"
            Layout.fillWidth: true
            title: qsTr("Identificação do Produto")
            product: root.product
            showOverlays: root.showDevOverlays

            Zone {
                tag: zoneTagMap["viewer_identification_code"]
                title: qsTr("Código")
                zoneType: "bloco-dados-gerais"
                widgetType: "campo"
                widgetQtClass: "QLineEdits"
                metadataKey: "code"
                product: identificationBlock.product
                showOverlays: identificationBlock.showOverlays
            }

            Zone {
                tag: zoneTagMap["viewer_identification_name"]
                title: qsTr("Designação")
                zoneType: "bloco-dados-gerais"
                widgetType: "campo"
                widgetQtClass: "QLineEdits"
                metadataKey: "name"
                product: identificationBlock.product
                showOverlays: identificationBlock.showOverlays
            }
        }

        Block {
            id: technicalBlock
            objectName: "block_dados_tecnicos"
            Layout.fillWidth: true
            title: qsTr("Dados Técnicos")
            product: root.product
            showOverlays: root.showDevOverlays

            Zone {
                tag: zoneTagMap["viewer_technical_state"]
                title: qsTr("Estado")
                zoneType: "bloco-ingredientes"
                widgetType: "tabela"
                widgetQtClass: "QTableViews"
                metadataKey: "estado"
                product: technicalBlock.product
                showOverlays: technicalBlock.showOverlays
            }

            Zone {
                tag: zoneTagMap["viewer_technical_validity"]
                title: qsTr("Validade")
                zoneType: "bloco-ingredientes"
                widgetType: "tabela"
                widgetQtClass: "QTableViews"
                metadataKey: "validade"
                product: technicalBlock.product
                showOverlays: technicalBlock.showOverlays
            }
        }

        Block {
            id: ingredientsBlock
            objectName: "block_ingredientes"
            Layout.fillWidth: true
            title: qsTr("Ficha Técnica")
            product: root.product
            showOverlays: root.showDevOverlays

            Zone {
                id: ingredientsZone
                tag: zoneTagMap["ingredients_root"]
                title: qsTr("Ingredientes")
                zoneType: "bloco-ingredientes"
                widgetType: "tabela"
                widgetQtClass: "QTableViews"
                metadataKey: ""
                product: ingredientsBlock.product
                showOverlays: ingredientsBlock.showOverlays

                ColumnLayout {
                    id: ingredientsContent
                    Layout.fillWidth: true
                    spacing: 3

                    IngredientRow {
                        Layout.fillWidth: true
                        header: true
                        ingredientName: qsTr("INGREDIENTE")
                        quantity: qsTr("QUANTIDADE")
                        unit: qsTr("UNIDADE")
                        ppu: qsTr("PPU")
                        total: qsTr("TOTAL")
                        showOverlays: ingredientsZone.showOverlays
                        zoneType: ingredientsZone.zoneType
                        visible: ingredientsRepeater.count > 0
                    }

                    Repeater {
                        id: ingredientsRepeater
                        model: ingredientsBlock.product && ingredientsBlock.product.ingredients ? ingredientsBlock.product.ingredients : []

                        IngredientRow {
                            Layout.fillWidth: true
                            ingredientName: modelData.name || modelData.ingredient || modelData.ComponenteNome || ""
                            quantity: modelData.quantity !== undefined ? modelData.quantity : (modelData.Qtd !== undefined ? modelData.Qtd : "")
                            unit: modelData.unit || modelData.Unidade || ""
                            ppu: modelData.ppu !== undefined ? modelData.ppu : (modelData.Ppu !== undefined ? modelData.Ppu : "")
                            total: modelData.total !== undefined ? modelData.total : (modelData.Preco !== undefined ? modelData.Preco : "")
                            showOverlays: ingredientsZone.showOverlays
                            zoneType: ingredientsZone.zoneType
                        }
                    }

                    Label {
                        Layout.fillWidth: true
                        text: qsTr("Sem ingredientes disponíveis")
                        color: "#6b778c"
                        font.italic: true
                        horizontalAlignment: Text.AlignHCenter
                        visible: ingredientsRepeater.count === 0
                    }
                }
            }
        }

        Block {
            id: overlayBlock
            objectName: "block_overlays"
            Layout.fillWidth: true
            title: qsTr("Informação Complementar")
            product: root.product
            showOverlays: root.showDevOverlays

            Zone {
                tag: zoneTagMap["food_cost_observations"]
                title: qsTr("Observações")
                zoneType: "bloco-food-cost"
                widgetType: "campo"
                widgetQtClass: "QLineEdits"
                metadataKey: "observacoes"
                product: overlayBlock.product
                showOverlays: overlayBlock.showOverlays
            }
        }

        Item {
            Layout.fillHeight: true
            Layout.fillWidth: true
        }
    }
}
