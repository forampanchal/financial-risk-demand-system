def assign_risk(z):
    if abs(z) < 1:
        return "LOW"
    elif abs(z) < 2:
        return "MEDIUM"
    elif abs(z) < 3:
        return "HIGH"
    else:
        return "CRITICAL"
