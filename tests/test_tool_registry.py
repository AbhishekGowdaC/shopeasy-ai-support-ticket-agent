
import pytest

from app.tools.tool_registry import execute_tool


def test_execute_order_tool():
    result = execute_tool(
        "get_order_details",
        {"order_id": "ORD1001"}
    )

    assert result["success"] is True


def test_unknown_tool():
    with pytest.raises(ValueError):
        execute_tool("delete_database", {})


def test_missing_order_id():
    with pytest.raises(ValueError):
        execute_tool("get_order_details", {})


def test_invalid_arguments():
    with pytest.raises(ValueError):
        execute_tool("get_order_details", "ORD1001")


def test_invalid_order_id_type():
    with pytest.raises(ValueError):
        execute_tool(
            "get_order_details",
            {"order_id": 123}
        )
