def format_ticket_number(prefix: str, sequence_number: int) -> str:
    return f"{prefix}-{sequence_number}"


def get_proximity_tier(position: int) -> int:
    if not position or position < 1:
        return 0
    return position if position <= 3 else 0


def get_wait_band(position: int) -> str:
    if not position or position < 1:
        return "—"
    if position == 1:
        return "0–5 min"
    if position == 2:
        return "5–10 min"
    if position == 3:
        return "10–15 min"
    return ">15 min"
