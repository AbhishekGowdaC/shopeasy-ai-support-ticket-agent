import pytest

from app.agent.execution_limits import (
    MAX_AGENT_STEPS,
    check_step_limit
)


def test_execution_within_limit():

    assert check_step_limit(3) is True


def test_execution_at_limit():

    with pytest.raises(RuntimeError):

        check_step_limit(MAX_AGENT_STEPS)