from datetime import datetime
from timeslot import *
def generate_timeslots(start_date, end_date, daily_slots):
    timeslots = []
    timeslot_id = 1
    current_date = start_date
    
    time_pairs = [
        ("09:00", "11:00"),
        ("12:00", "02:00"),
        ("15:00", "17:00"),
    ]
    
    while current_date <= end_date:
        # Skip weekends (Friday and Saturday)
        if current_date.weekday() not in [4, 5]:  # 4 = Friday, 5 = Saturday
            for i in range(min(daily_slots, len(time_pairs))):
                start_time, end_time = time_pairs[i]
                timeslots.append(
                    Timeslot(timeslot_id, current_date, start_time, end_time)
                )
                timeslot_id += 1
        
        current_date += timedelta(days=1)
    
    return timeslots

# ==== Define Exam Period ====
start_date = datetime(2025, 5, 19)
end_date = datetime(2025, 6, 4)
daily_slots = 3
# ==== Generate Timeslots ====
timeslots = generate_timeslots(start_date, end_date, daily_slots)
