from datetime import datetime, timedelta

class Timeslot:
    def __init__(self, timeslot_id: int, date: datetime, start_time: str, end_time: str):
        self.timeslot_id = timeslot_id
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        
    @property
    def day(self):
        return self.date.strftime("%A")
    
    @property
    def date_str(self):
        return self.date.strftime("%Y-%m-%d")
    
    @property
    def time_str(self):
        return f"{self.start_time}-{self.end_time}"