ORDERS = {
    "ORD1001": {
        "order_id": "ORD1001",
        "product": "Wireless Headphones",
        "status": "SHIPPED",
        "delivery_date": "2026-11-27",
        "amount": 2500
    },
    "ORD1002": {
        "order_id": "ORD1002",
        "product": "Smart Watch",
        "status": "PROCESSING",
        "delivery_date": "2026-11-30",
        "amount": 4500
    },
    "ORD1003": {
        "order_id": "ORD1003",
        "product": "Keyboard",
        "status": "DELIVERED",
        "delivery_date": "2026-11-20",
        "amount": 1500
    }
}


def get_order_details(order_id: str) -> dict:

    if not order_id.strip():
        raise ValueError("Order ID cannot be empty")

    order = ORDERS.get(order_id.strip().upper())

    if order is None:
        return {
            "success": False,
            "message": "Order not found"
        }

    return {
        "success": True,
        "order": order
    }
