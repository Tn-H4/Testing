#Time
def time_strings(dt):
    hour = dt.strftime("%I").lstrip("0") or "0"
    minute = dt.strftime("%M")
    ampm = dt.strftime("%p")
    t_str = f"{hour}:{minute} {ampm}"
    d_str = dt.strftime("%m/%d/%Y")
    return t_str, d_str
