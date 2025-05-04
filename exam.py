from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Tuple, Set

from room import Room
from timeslot import Timeslot

class Exam:
    def __init__(self, exam_id: int, course_name: str, duration: int, students: list, priority: int):
        self.exam_id = exam_id
        self.course_name = course_name
        self.duration = duration
        self.students = students
        self.priority = priority  # Higher priority exams should be scheduled first
        self.difficulty = priority  # Using priority as difficulty for now

@dataclass
class ExamAssignment:
    """Represents an exam assignment to specific rooms and timeslots"""
    exam: Exam
    timeslots: List['Timeslot']  # An exam can span multiple timeslots
    rooms: List['Room']  # An exam can be assigned to multiple rooms
    
    def get_total_capacity(self) -> int:
        """Calculate total capacity of all assigned rooms"""
        return sum(room.capacity for room in self.rooms)
    
    def has_enough_capacity(self) -> bool:
        """Check if assigned rooms have enough capacity for all students"""
        return self.get_total_capacity() >= len(self.exam.students)
    
    def get_duration_hours(self) -> float:
        """Calculate total duration in hours"""
        if not self.timeslots:
            return 0
        
        # If we have multiple timeslots, calculate based on time difference
        if len(self.timeslots) > 1:
            first_start = datetime.strptime(self.timeslots[0].start_time, "%H:%M")
            last_end = datetime.strptime(self.timeslots[-1].end_time, "%H:%M")
            return (last_end - first_start).total_seconds() / 3600
        
        # For single timeslot, use the time difference
        start_time = datetime.strptime(self.timeslots[0].start_time, "%H:%M")
        end_time = datetime.strptime(self.timeslots[0].end_time, "%H:%M")
        return (end_time - start_time).total_seconds() / 3600
