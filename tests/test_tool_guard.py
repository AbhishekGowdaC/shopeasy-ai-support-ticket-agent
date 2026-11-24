import pytest
from app.guardrails.tool_guard import validate_tool_call, validate_refund_amount


def test_allowed_tool():
    assert validate_tool_call("get_order_details") is True


def test_disallowed_tool():
    with pytest.raises(PermissionError):
        validate_tool_call("delete_customer_database")


def test_refund_tool_is_allowed():
    assert validate_tool_call("process_refund") is True



def test_valid_refund_amount():
    assert validate_refund_amount(5000) is True


def test_negative_refund_amount():
    with pytest.raises(ValueError):
        validate_refund_amount(-500)


def test_high_refund_amount():
    with pytest.raises(PermissionError):
        validate_refund_amount(15000)
