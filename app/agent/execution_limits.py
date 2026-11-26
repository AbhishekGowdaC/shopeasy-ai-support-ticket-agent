MAX_AGENT_STEPS = 5


def check_step_limit(current_step):

    if current_step > MAX_AGENT_STEPS:
        raise RuntimeError(
            "Maximum agent execution steps exceeded"
        )

    return True


MAX_TOOL_CALLS = 3


def check_tool_limit(current_tool_calls):

    if current_tool_calls > MAX_TOOL_CALLS:
        raise RuntimeError(
            "Maximum agent tool calls exceeded"
        )

    return True