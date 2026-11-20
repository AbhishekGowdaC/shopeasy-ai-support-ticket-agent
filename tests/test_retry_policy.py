
from app.agent.retry_policy import calculate_retry_delay


def test_first_retry_delay():
    delay = calculate_retry_delay(1)

    assert 2 <= delay <= 3


def test_second_retry_delay():
    delay = calculate_retry_delay(2)

    assert 4 <= delay <= 5


def test_third_retry_delay():
    delay = calculate_retry_delay(3)

    assert 8 <= delay <= 9


def test_maximum_retry_delay():
    delay = calculate_retry_delay(10)

    assert delay <= 61
