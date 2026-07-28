# Utilities for calculations

def pace_to_speed(pace):
    """
    Convert pace (minutes per mile) to speed (miles per hour).
    """
    if pace <= 0:
        raise ValueError("Pace must be greater than zero.")
    return 60 / pace

def speed_to_pace(speed):
    """
    Convert speed (miles per hour) to pace (minutes per mile).
    """
    if speed <= 0:
        raise ValueError("Speed must be greater than zero.")
    return 60 / speed 

def speed_to_bpm(speed):
    """
    Convert speed (miles per hour) to beats per minute (BPM).
    This is pulled from www.stepscal.com/mph-to-steps-calculator and assumes an average height of 170cm (5'7").
    """
    if speed <= 0:
        raise ValueError("Speed must be greater than zero.")
    elif speed <= 4:
        # Walking speed (<=4 mph)
        bpm = speed * 1609.34 / 60 / (170 * 0.414 / 100)
    else:
        # Running speed (>4 mph)
        bpm = speed * 1609.34 / 60 / (170 * 0.45 / 100)

    return bpm

def bpm_to_speed(bpm):
    """
    Convert beats per minute (BPM) to speed (miles per hour).
    This is pulled from www.stepscal.com/mph-to-steps-calculator and assumes an average height of 170cm (5'7").
    """
    if bpm <= 0:
        raise ValueError("BPM must be greater than zero.")
    elif bpm <= 160:
        # Walking speed (<=4 mph)
        speed = bpm * (170 * 0.414 / 100) * 60 / 1609.34
    else:
        # Running speed (>4 mph)
        speed = bpm * (170 * 0.45 / 100) * 60 / 1609.34

    return speed