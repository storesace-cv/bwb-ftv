from utils.formatting import parse_decimal


def test_parse_decimal_nbsp():
    assert parse_decimal("1\u00A0234,56") == 1234.56
