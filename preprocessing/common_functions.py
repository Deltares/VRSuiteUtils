def check_string_in_list(str, list_vals):
    for item in list_vals:
        if item in str:
            return True
    return False
