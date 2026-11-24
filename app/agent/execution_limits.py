MAX_AGENT_STEPS = 5


def check_step_limit(current_step):

    if current_step >= MAX_AGENT_STEPS:
        raise RuntimeError(
            "Maximum agent execution steps exceeded"
        )

    return True