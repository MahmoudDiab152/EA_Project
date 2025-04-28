class Exam:
    def __init__(self, exam_id: int, course_name: str, duration: int, students: list, difficulty: int):
        self.exam_id = exam_id
        self.course_name = course_name
        self.duration = duration  # minutes
        self.students = students  
        self.difficulty = difficulty
