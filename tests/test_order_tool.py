
import pytest

from app.tools.order_tool import get_order_details


def test_existing_order():
    result = get_order_details("ORD1001")

    assert result["success"] is True
    assert result["order"]["product"] == "Wireless Headphones"


def test_order_not_found():
    result = get_order_details("ORD9999")

    assert result["success"] is False


def test_order_id_case_insensitive():
    result = get_order_details("ord1001")

    assert result["success"] is True


def test_empty_order_id():
    with pytest.raises(ValueError):
        get_order_details("")


def test_order_id_with_whitespace():
    result = get_order_details(" ORD1001 ")

    assert result["success"] is True
