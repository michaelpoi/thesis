def get_termination_reason(agent_info: dict) -> str:
    # Keep only needed keys
    possible_reasons = ["crash_vehicle", 
                        "out_of_road", 
                        "arrive_dest", 
                        "max_step"]

    for reason in possible_reasons:
        if agent_info.get(reason, False):
            return reason
    return "unknown"