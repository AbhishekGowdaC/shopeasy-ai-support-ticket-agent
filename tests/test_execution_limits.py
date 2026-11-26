import pytest

from app.agent.execution_limits import (
    MAX_AGENT_STEPS,
    check_step_limit
)

from app.agent.execution_limits import (
    MAX_TOOL_CALLS,
    check_tool_limit
)

def test_execution_within_limit():
    assert check_step_limit(3) is True


def test_execution_at_limit():
    assert check_step_limit(MAX_AGENT_STEPS) is True


def test_execution_exceeds_limit():
    with pytest.raises(RuntimeError):
        check_step_limit(MAX_AGENT_STEPS + 1)


def test_tool_calls_within_limit():
    assert check_tool_limit(2) is True


def test_tool_calls_at_limit():
    assert check_tool_limit(MAX_TOOL_CALLS) is True


def test_tool_calls_exceed_limit():
    with pytest.raises(RuntimeError):
        check_tool_limit(MAX_TOOL_CALLS + 1)