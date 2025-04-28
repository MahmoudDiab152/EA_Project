class Timetable:
    def __init__(self, exams=None, rooms=None, timeslots=None):
        # Initialize with an empty schedule
        self.schedule = {}  # exam_id -> (room, timeslot)