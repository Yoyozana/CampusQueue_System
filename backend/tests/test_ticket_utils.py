from utils.ticket import format_ticket_number, get_proximity_tier, get_wait_band

assert format_ticket_number("REG", 1) == "REG-1"
print("PASS: format_ticket_number ->", format_ticket_number("REG", 1))

assert get_proximity_tier(1) == 1
assert get_proximity_tier(4) == 0
print("PASS: get_proximity_tier boundaries correct")

assert get_wait_band(1) == "0–5 min"
assert get_wait_band(4) == ">15 min"
print("PASS: get_wait_band matches spec table")

print("ALL TESTS PASSED")
