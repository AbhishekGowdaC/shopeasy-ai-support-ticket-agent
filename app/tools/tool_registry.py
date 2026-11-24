
from app.tools.order_tool import get_order_details


TOOLS = {
    "get_order_details": get_order_details
}


def execute_tool(tool_name: str, arguments: dict) -> dict:

    tool = TOOLS.get(tool_name)

    if tool is None:
        raise ValueError(f"Unknown tool: {tool_name}")

    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a dictionary")

    if tool_name == "get_order_details":
        order_id = arguments.get("order_id")

        if not isinstance(order_id, str):
            raise ValueError("order_id must be a string")

        return tool(order_id)

    raise ValueError("Tool execution is not supported")
