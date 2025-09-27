# Changelog

## [2025-09-27]

### Added
- Documented that ReportBro template `ft_gestao_02.json` agora inclui uma tabela
  de ingredientes alimentada pelo dataset `${ingredientes}`, com conversão
  numérica garantida por `reporting/ft_gestao.build_reportbro_context` e
  coberta pelos testes de exportação em `tests/test_reportbro_export.py`.

## [2025-09-26]

### Added
- Introduced product image integration in ReportBro template `ft_gestao_02.json`.
- New parameter `product_image_filename` defined with fixed path rules: `/databases/images/{Produtos_Codigo}.png`.
- Updated **README.md** with documentation for product image handling.
- Updated **AGENTS.md** with new **ReportBro Image Verification Agent**.
- Updated **reportbro_schema_from_template.md** with explicit reference to `product_image_filename`.
