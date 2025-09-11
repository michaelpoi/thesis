def get_termination_reason(agent_info: dict) -> str:
    # Keep only needed keys
    if agent_info.get("crash_vehicle", False):
        return "crash_vehicle"
    elif agent_info.get("out_of_road", False):
        return "out_of_road"
    elif agent_info.get("arrive_dest", False):
        return "arrive_dest"
    else:
        return "unknown"