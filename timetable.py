class Timetable:
        def __init__(self, decoded_solution):
            self.schedule = {}
            for assignment in decoded_solution:
                if 'exam' in assignment and 'timeslots' in assignment and 'rooms' in assignment:
                    self.schedule[assignment['exam'].exam_id] = (
                        assignment['rooms'],
                        assignment['timeslots']
                    )