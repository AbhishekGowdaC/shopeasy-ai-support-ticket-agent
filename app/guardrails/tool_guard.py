
ALLOWED_TOOLS = {
    "get_order_details",
    "check_delivery_status",
    "process_refund"
}


def validate_tool_call(tool_name: str) -> bool:
    if tool_name not in ALLOWED_TOOLS:
        raise PermissionError(
            f"Tool '{tool_name}' is not allowed"
        )

    return True


def validate_refund_amount(amount: float) -> bool:
    if amount <= 0:
        raise ValueError("Refund amount must be positive")

    if amount > 10000:
        raise PermissionError(
            "Refund requires human approval"
        )

    return True
