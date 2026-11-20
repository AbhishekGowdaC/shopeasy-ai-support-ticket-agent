import pytest
from pydantic import ValidationError

from app.schemas.ticket import TicketCreate

VALID = {
    "customer_name": "Asha Rao",
    "email": "asha@example.com",
    "subject": "Double charge",
    "message": "I was charged twice for my order.",
}


def make_ticket(**overrides):
    """Build a TicketCreate from valid defaults plus any overrides."""
    return TicketCreate(**{**VALID, **overrides})


# 1. Valid ticket accepted
def test_valid_ticket_is_accepted():
    ticket = make_ticket()
    assert ticket.customer_name == "Asha Rao"
    assert ticket.email == "asha@example.com"
    assert ticket.order_id is None


# 2. Invalid email rejected
def test_invalid_email_is_rejected():
    with pytest.raises(ValidationError) as exc:
        make_ticket(email="not-an-email")
    assert "email" in str(exc.value)


# 3. Empty message rejected (empty string and whitespace-only)
@pytest.mark.parametrize("bad_message", ["", "     ", "\n\t  \n"])
def test_empty_message_is_rejected(bad_message):
    with pytest.raises(ValidationError):
        make_ticket(message=bad_message)


# 4. Message over 3,000 characters rejected (and exactly 3,000 accepted)
def test_message_over_3000_characters_is_rejected():
    with pytest.raises(ValidationError):
        make_ticket(message="x" * 3001)


def test_message_of_exactly_3000_characters_is_accepted():
    ticket = make_ticket(message="x" * 3000)
    assert len(ticket.message) == 3000


# 5. Control characters removed
def test_control_characters_are_removed():
    ticket = make_ticket(message="Hello\x00 there\x07, my order\x1f is late")
    assert ticket.message == "Hello there, my order is late"


def test_newline_and_tab_are_preserved():
    ticket = make_ticket(message="Line one\nLine two\tindented")
    assert ticket.message == "Line one\nLine two\tindented"


# 6. order_id "#4521" becomes "4521"
def test_order_id_leading_hash_is_removed():
    ticket = make_ticket(order_id="#4521")
    assert ticket.order_id == "4521"


# 7. order_id "###4521" rejected
def test_order_id_with_multiple_hashes_is_rejected():
    with pytest.raises(ValidationError):
        make_ticket(order_id="###4521")

def test_unicode_compatibility_characters_are_normalized():
    ticket = make_ticket(subject="Ｆｕｌｌ Ｗｉｄｔｈ")
    assert ticket.subject == "Full Width"