from datetime import datetime, timedelta
from timeslot import Timeslot
from data import Data
from visualize import visualize_timetable
# === Fitness Function ===
def get_fitness(timetable, exams):
    penalty = 0

    # Check for student conflicts (same student in two exams at the same time)
    student_schedule = {}  # (student_id, date, timeslot_id) -> exam_id
    
    for exam_id, (room, timeslot) in timetable.schedule.items():
        exam = next(e for e in exams if e.exam_id == exam_id)
        
        # Check if room is big enough for all students
        if len(exam.students) > room.capacity:
            penalty += 20  # Severe penalty for room capacity violations
        
        # Check for student scheduling conflicts
        for student in exam.students:
            key = (student.student_id, timeslot.date_str, timeslot.timeslot_id)
            if key in student_schedule:
                # Student has two exams at the same time
                penalty += 50
            else:
                student_schedule[key] = exam_id
                
            # Check for consecutive exams on the same day
            same_day_key = (student.student_id, timeslot.date_str)
            student_exams_on_day = [
                (tid, eid) for (sid, date, tid), eid in student_schedule.items() 
                if sid == student.student_id and date == timeslot.date_str
            ]
            
            for other_timeslot_id, other_exam_id in student_exams_on_day:
                if other_timeslot_id != timeslot.timeslot_id:
                    # Add penalty for consecutive exams (less severe than direct conflict)
                    penalty += 15

    # Difficulty balancing - penalize having difficult exams on the same day
    exams_by_date = {}
    for exam_id, (room, timeslot) in timetable.schedule.items():
        exam = next(e for e in exams if e.exam_id == exam_id)
        if timeslot.date_str not in exams_by_date:
            exams_by_date[timeslot.date_str] = []
        exams_by_date[timeslot.date_str].append((exam, timeslot))
    
    # Penalize if difficult exams are scheduled on the same day
    for date, date_exams in exams_by_date.items():
        if len(date_exams) > 1:
            total_difficulty = sum(exam.difficulty for exam, _ in date_exams)
            if total_difficulty > 15:  # Arbitrary threshold
                penalty += (total_difficulty - 15) * 2
    
    # Return negative penalty as fitness (higher is better)
    return -penalty
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



if __name__ == "__main__":
    # ==== Read Data ====
    students = Data.read_students()
    rooms = Data.read_rooms()
    exams = Data.read_exams(students)

    # ==== Define Exam Period ====
    start_date = datetime(2025, 5, 12)
    end_date = datetime(2025, 5, 23)
    daily_slots = 3
    print(exams)
    # ==== Generate Timeslots ====
    timeslots = generate_timeslots(start_date, end_date, daily_slots)
    print(f"Generated {len(timeslots)} timeslots between {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')}")

    # ==== Run Optimization Algorithm ====
    optimalFitness = 0
    best_timetable = Algorithm(exams, rooms, timeslots, optimalFitness, max_iterations=2000)

    # ==== Visualize the Best Timetable ====
    visualize_timetable(best_timetable, exams, timeslots, rooms)

