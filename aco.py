import random
from datetime import datetime
from Time_Slots import generate_timeslots, timeslots
from encoder import create_encoded_lists, decode_individual
from data import Data
import room

class ACO:
    def __init__(self):
        # Read data for decoding/encoding
        self.students = Data.read_students()
        self.exams = Data.read_exams(self.students)
        self.rooms = Data.read_rooms()
        self.time_slots = timeslots
        
        # Create encoded lists for solution representation
        self.encoded_courses, self.encoded_time_slots, self.encoded_halls = create_encoded_lists(
            self.exams, self.time_slots, self.rooms
        )
        
        # ACO parameters
        self.num_ants = 20
        self.alpha = 0.9  # pheromone importance
        self.beta = 2.8   # heuristic importance
        self.evaporation_rate = 0.5
        self.Q = 100      # pheromone deposit scaling
        
        # Pheromone limits
        self.min_pheromone = 0.1
        self.max_pheromone = 10.0
        
        # Initialize pheromone trails
        self.pheromone = {}
        self._initialize_pheromones()
        
        # Tracking conflict information
        self.student_conflicts = []  # [(student_id, date, timeslot_id, exam1_id, exam2_id), ...]
        self.room_conflicts = []     # [(room_id, date, timeslot_id, exam1_id, exam2_id), ...]
        self.consecutive_exams = []  # [(student_id, date, [exam_ids]), ...]
        self.capacity_issues = []    # [(exam_id, needed_capacity, available_capacity), ...]
        self.non_consecutive_slots = [] # [(exam_id, [timeslot_ids]), ...]
        self.conflict_stats = {}
    
    def _initialize_pheromones(self):
        """Initialize all pheromone trails to the same value"""
        # For each exam, timeslot combination, and room combination
        for i, exam in enumerate(self.exams):
            exam_code = f"C{i+1}"
            for ts in self.encoded_time_slots:
                for room_id in self.encoded_halls:
                    key = (exam_code, ts, room_id)
                    self.pheromone[key] = 1.0
    
    def run_aco(self, num_iterations=100, num_ants=20, local_search_iterations=10):
        print(f"Starting ACO with {num_ants} ants for {num_iterations} iterations")
        
        self.num_ants = num_ants
        best_solution = None
        best_decoded = None
        best_fitness = float('-inf')
        
        for iteration in range(num_iterations):
            solutions = []
            fitness_scores = []
            
            # Each ant constructs a solution
            for ant in range(self.num_ants):
                solution = self.construct_solution()
                solution = self.local_search(solution, iterations=local_search_iterations)
                
                # Decode solution for evaluation
                decoded = decode_individual(solution, self.rooms, self.time_slots, self.exams)
                fitness = self.get_fitness(decoded, self.exams)
                
                solutions.append(solution)
                fitness_scores.append(fitness)
                
                # Track best solution
                if fitness > best_fitness:
                    best_fitness = fitness
                    best_solution = solution
                    best_decoded = decoded
                    # Get conflicts of best solution
                    self.get_fitness(best_decoded, self.exams)
            
            # Print iteration info
            print(f"Iteration {iteration + 1}: Best Fitness = {max(fitness_scores)}")
            
            # Update pheromone trails
            self.update_pheromones(solutions, fitness_scores)
        
        # Final evaluation of best solution
        best_decoded = decode_individual(best_solution, self.rooms, self.time_slots, self.exams)
        _ = self.get_fitness(best_decoded, self.exams)
        
        # Print conflict report
        self.print_conflict_report()
        
        return best_solution, iteration, best_decoded
    
    def construct_solution(self):
        """Construct a solution for one ant"""
        solution = []
        
        for i, exam in enumerate(self.exams):
            exam_code = f"C{i+1}"
            
            # Calculate required number of slots based on exam duration
            required_slots = max(1, exam.duration // 120)  # Assuming 2 hours per slot
            
            # Find possible timeslot combinations (consecutive slots)
            possible_timeslots = self.get_possible_timeslot_combinations(required_slots)
            
            # Calculate required room capacity
            required_capacity = len(exam.students)
            
            # Find possible room combinations
            possible_rooms = self.get_possible_room_combinations(required_capacity)
            
            # Calculate selection probabilities
            options = []
            probabilities = []
            
            for ts_combination in possible_timeslots:
                ts_str = "+".join(ts_combination)
                
                for room_combination in possible_rooms:
                    room_str = "+".join(room_combination)
                    
                    # Calculate pheromone value (average of all combinations)
                    pheromone_value = 0
                    count = 0
                    for ts in ts_combination:
                        for room_id in room_combination:
                            key = (exam_code, ts, room_id)
                            if key in self.pheromone:
                                pheromone_value += self.pheromone[key]
                                count += 1
                    
                    if count > 0:
                        pheromone_value /= count
                    else:
                        pheromone_value = self.min_pheromone
                    
                    # Calculate heuristic value
                    temp_solution = solution.copy()
                    temp_solution.append(f"{exam_code}-{ts_str}-{room_str}")
                    temp_decoded = decode_individual(temp_solution, self.rooms, self.time_slots, self.exams)
                    
                    # Use inverse of penalty as heuristic
                    heuristic_value = 1.0 / (1.0 - min(self.get_fitness(temp_decoded, self.exams), -1))
                    
                    # Calculate probability
                    probability = (pheromone_value ** self.alpha) * (heuristic_value ** self.beta)
                    
                    options.append((ts_str, room_str))
                    probabilities.append(probability)
            
            # If no valid options, create a random assignment
            if not options:
                ts_combination = random.sample(self.encoded_time_slots, min(required_slots, len(self.encoded_time_slots)))
                room_combination = random.sample(self.encoded_halls, min(3, len(self.encoded_halls)))
                
                ts_str = "+".join(sorted(ts_combination, key=lambda x: int(x[2:])))
                room_str = "+".join(room_combination)
                
                assignment = f"{exam_code}-{ts_str}-{room_str}"
            else:
                # Normalize probabilities
                total = sum(probabilities)
                if total > 0:
                    probabilities = [p / total for p in probabilities]
                else:
                    probabilities = [1.0 / len(options)] * len(options)
                
                # Select based on probabilities
                selected_index = 0
                if len(options) > 1:
                    selected_index = random.choices(range(len(options)), weights=probabilities, k=1)[0]
                
                ts_str, room_str = options[selected_index]
                assignment = f"{exam_code}-{ts_str}-{room_str}"
            
            solution.append(assignment)
        
        return solution
    
    def get_possible_timeslot_combinations(self, required_slots):
        """Generate possible combinations of consecutive timeslots"""
        if required_slots <= 0:
            return [[]]
        
        if required_slots == 1:
            return [[ts] for ts in self.encoded_time_slots]
        
        # Group timeslots by date
        timeslots_by_date = {}
        for ts in self.time_slots:
            if ts.date_str not in timeslots_by_date:
                timeslots_by_date[ts.date_str] = []
            timeslots_by_date[ts.date_str].append(ts)
        
        # Sort timeslots by ID for each date
        for date, slots in timeslots_by_date.items():
            timeslots_by_date[date] = sorted(slots, key=lambda ts: ts.timeslot_id)
        
        combinations = []
        
        # Find consecutive timeslots for each date
        for date, slots in timeslots_by_date.items():
            for i in range(len(slots) - required_slots + 1):
                consecutive_slots = slots[i:i + required_slots]
                combination = [f"TS{ts.timeslot_id}" for ts in consecutive_slots]
                combinations.append(combination)
        
        # Limit the number of combinations to avoid computational explosion
        if len(combinations) > 20:
            combinations = random.sample(combinations, 20)
        
        return combinations if combinations else [[f"TS{random.randint(1, len(self.time_slots))}"]]
    
    def get_possible_room_combinations(self, required_capacity):
        """Generate possible combinations of rooms to meet capacity requirements"""
        sorted_rooms = sorted(self.rooms, key=lambda r: r.capacity, reverse=True)
        room_combinations = []
        
        # Single room solution
        for room in sorted_rooms:
            if room.capacity >= required_capacity:
                room_combinations.append([f"R{room.room_id}"])
                
                # Limit the number of single room solutions
                if len(room_combinations) >= 5:
                    break
        
        # Two room solution
        if not room_combinations or len(room_combinations) < 3:
            for i, room1 in enumerate(sorted_rooms):
                for room2 in sorted_rooms[i+1:]:
                    if room1.capacity + room2.capacity >= required_capacity:
                        room_combinations.append([f"R{room1.room_id}", f"R{room2.room_id}"])
                        
                        # Limit the number of combinations
                        if len(room_combinations) >= 10:
                            break
                if len(room_combinations) >= 10:
                    break
        
        # Three room solution if needed
        if not room_combinations:
            # Just pick 3 largest rooms
            top_rooms = sorted_rooms[:3]
            room_combinations.append([f"R{room.room_id}" for room in top_rooms])
        
        # Ensure we have at least one combination
        if not room_combinations:
            room_combinations.append([f"R{random.randint(1, len(self.rooms))}"])
        
        return room_combinations
    
    def local_search(self, solution, iterations=10):
        """Apply local search to improve the solution"""
        best_solution = solution.copy()
        best_decoded = decode_individual(best_solution, self.rooms, self.time_slots, self.exams)
        best_fitness = self.get_fitness(best_decoded, self.exams)
        
        for _ in range(iterations):
            # Choose a random improvement strategy
            strategy = random.choice(["swap_exams", "change_room", "change_timeslot"])
            
            if strategy == "swap_exams" and len(solution) >= 2:
                # Swap two random exams
                i, j = random.sample(range(len(solution)), 2)
                
                new_solution = best_solution.copy()
                new_solution[i], new_solution[j] = new_solution[j], new_solution[i]
                
            elif strategy == "change_room":
                # Change room for a random exam
                i = random.randint(0, len(solution) - 1)
                parts = solution[i].split('-')
                
                if len(parts) == 3:
                    exam_code = parts[0]
                    ts_str = parts[1]
                    
                    # Get a new room combination
                    exam_index = int(exam_code[1:]) - 1
                    exam = self.exams[exam_index]
                    required_capacity = len(exam.students)
                    
                    possible_rooms = self.get_possible_room_combinations(required_capacity)
                    new_room_str = random.choice(possible_rooms)[0]
                    
                    new_solution = best_solution.copy()
                    new_solution[i] = f"{exam_code}-{ts_str}-{new_room_str}"
                else:
                    continue
                
            elif strategy == "change_timeslot":
                # Change timeslot for a random exam
                i = random.randint(0, len(solution) - 1)
                parts = solution[i].split('-')
                
                if len(parts) == 3:
                    exam_code = parts[0]
                    room_str = parts[2]
                    
                    # Get a new timeslot combination
                    exam_index = int(exam_code[1:]) - 1
                    exam = self.exams[exam_index]
                    required_slots = max(1, exam.duration // 120)
                    
                    possible_timeslots = self.get_possible_timeslot_combinations(required_slots)
                    new_ts_str = "+".join(random.choice(possible_timeslots))
                    
                    new_solution = best_solution.copy()
                    new_solution[i] = f"{exam_code}-{new_ts_str}-{room_str}"
                else:
                    continue
            else:
                continue
            
            # Evaluate the new solution
            new_decoded = decode_individual(new_solution, self.rooms, self.time_slots, self.exams)
            new_fitness = self.get_fitness(new_decoded, self.exams)
            
            # Update if better
            if new_fitness > best_fitness:
                best_solution = new_solution
                best_fitness = new_fitness
                best_decoded = new_decoded
        
        return best_solution
    
    def update_pheromones(self, solutions, fitness_scores):
        """Update pheromone trails based on solution quality"""
        # Evaporate all pheromones
        for key in self.pheromone:
            self.pheromone[key] *= (1 - self.evaporation_rate)
            self.pheromone[key] = max(self.min_pheromone, self.pheromone[key])
        
        # Add new pheromones based on solution quality
        for solution, fitness in zip(solutions, fitness_scores):
            # Convert fitness to positive value for pheromone deposit
            deposit = self.Q / (1 - min(fitness, -1))
            
            for assignment in solution:
                parts = assignment.split('-')
                if len(parts) == 3:
                    exam_code = parts[0]
                    timeslots = parts[1].split('+')
                    rooms = parts[2].split('+')
                    
                    # Update pheromone for each combination
                    for ts in timeslots:
                        for room_id in rooms:
                            key = (exam_code, ts, room_id)
                            if key in self.pheromone:
                                self.pheromone[key] += deposit
                                self.pheromone[key] = min(self.max_pheromone, self.pheromone[key])
    
    def get_fitness(self, decoded_timetable, exams):
        penalty = 0
        student_schedule = {}  # (student_id, date, timeslot_id) -> exam_id
        exams_by_date = {}     # date_str -> list of (exam, timeslots)
        room_assignments = {}  # (timeslot, room) -> exam_id
        
        # Tracking conflict information
        self.student_conflicts = []  # [(student_id, date, timeslot_id, exam1_id, exam2_id), ...]
        self.room_conflicts = []     # [(room_id, date, timeslot_id, exam1_id, exam2_id), ...]
        self.consecutive_exams = []  # [(student_id, date, [exam_ids]), ...]
        self.capacity_issues = []    # [(exam_id, needed_capacity, available_capacity), ...]
        self.non_consecutive_slots = [] # [(exam_id, [timeslot_ids]), ...]
        
        exam_dict = {exam.exam_id: exam for exam in exams}  # Faster lookup

        # Core penalty weights
        CAPACITY_WEIGHT = 20       # Penalty per student over capacity
        ROOM_CONFLICT_WEIGHT = 40  # Room double-booking
        STUDENT_CONFLICT_WEIGHT = 70  # Direct student conflict
        CONSECUTIVE_EXAMS_WEIGHT = 25  # Consecutive exams on same day
        TIMESLOT_CONSISTENCY_WEIGHT = 50  # Non-consecutive timeslots
        DIFFICULTY_WEIGHT = 3      # Weight for difficulty balancing
        
        # New penalties
        WEEKEND_PENALTY = 10       # Penalty for scheduling on weekends
        SPREAD_BONUS = -5          # Bonus for well-spread exams

        for assignment in decoded_timetable:
            try:
                exam = assignment['exam']
                timeslots = assignment['timeslots']
                rooms = assignment['rooms']
                
                # Skip if no timeslots or rooms
                if not timeslots or not rooms:
                    penalty += 200
                    continue
                
                # 1. Check total room capacity with progressive penalty
                total_capacity = sum(room.capacity for room in rooms)
                capacity_deficit = len(exam.students) - total_capacity
                if capacity_deficit > 0:
                    # Progressive penalty: gets worse as deficit increases
                    penalty += CAPACITY_WEIGHT * (capacity_deficit + (capacity_deficit ** 1.5) // 10)
                    self.capacity_issues.append((exam.exam_id, len(exam.students), total_capacity))
                
                # 2. Check room double-booking with specific timeslot tracking
                for timeslot in timeslots:
                    for room in rooms:
                        room_key = (timeslot.timeslot_id, room.room_id)
                        if room_key in room_assignments:
                            # If same exam, smaller penalty
                            existing_exam_id = room_assignments[room_key]
                            if existing_exam_id == exam.exam_id:
                                penalty += ROOM_CONFLICT_WEIGHT // 2
                            else:
                                penalty += ROOM_CONFLICT_WEIGHT
                                # Track the conflict
                                self.room_conflicts.append((
                                    room.room_id, 
                                    timeslot.date_str, 
                                    timeslot.timeslot_id, 
                                    existing_exam_id, 
                                    exam.exam_id
                                ))
                        else:
                            room_assignments[room_key] = exam.exam_id
                
                # 3. Check student conflicts with improved handling
                for student in exam.students:
                    # Track all of this student's exams for better conflict analysis
                    student_exams_by_date = {}
                    
                    for timeslot in timeslots:
                        key = (student.student_id, timeslot.date_str, timeslot.timeslot_id)
                        
                        # Direct conflict check
                        if key in student_schedule:
                            existing_exam = student_schedule[key]
                            if existing_exam != exam.exam_id:  # Different exams
                                penalty += STUDENT_CONFLICT_WEIGHT
                                # Track the conflict
                                self.student_conflicts.append((
                                    student.student_id, 
                                    timeslot.date_str, 
                                    timeslot.timeslot_id,
                                    existing_exam, 
                                    exam.exam_id
                                ))
                        else:
                            student_schedule[key] = exam.exam_id
                        
                        # Track by date for consecutive exam check
                        if timeslot.date_str not in student_exams_by_date:
                            student_exams_by_date[timeslot.date_str] = []
                        
                        if exam.exam_id not in student_exams_by_date[timeslot.date_str]:
                            student_exams_by_date[timeslot.date_str].append(exam.exam_id)
                    
                    # Check for multiple exams on same day - with progressive penalty
                    for date, day_exams in student_exams_by_date.items():
                        if len(day_exams) > 1:
                            # Progressive penalty: 1->0, 2->25, 3->75, 4->150...
                            penalty += CONSECUTIVE_EXAMS_WEIGHT * (len(day_exams) - 1) ** 2
                            # Track the consecutive exams
                            self.consecutive_exams.append((student.student_id, date, day_exams))
                
                # 4. Check if timeslots are consecutive and on same day
                if len(timeslots) > 1:
                    # Verify slots are consecutive and on same day
                    consecutive_slots = True
                    expected_ids = [timeslots[0].timeslot_id]
                    base_date = timeslots[0].date
                    
                    for i in range(1, len(timeslots)):
                        # Check if IDs are consecutive
                        if timeslots[i].timeslot_id != expected_ids[-1] + 1:
                            consecutive_slots = False
                        
                        # Check if all timeslots are on the same day
                        if timeslots[i].date != base_date:
                            consecutive_slots = False
                        
                        expected_ids.append(timeslots[i].timeslot_id)
                    
                    if not consecutive_slots:
                        penalty += TIMESLOT_CONSISTENCY_WEIGHT
                        self.non_consecutive_slots.append((
                            exam.exam_id, [ts.timeslot_id for ts in timeslots]
                        ))
                
                # Track exams by date for difficulty balancing
                if timeslots and timeslots[0].date_str not in exams_by_date:
                    exams_by_date[timeslots[0].date_str] = []
                
                if timeslots:
                    # Check for weekend penalty
                    if timeslots[0].date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                        penalty += WEEKEND_PENALTY
                    
                    exams_by_date[timeslots[0].date_str].append((exam, timeslots))
                
            except (KeyError, AttributeError) as e:
                penalty += 150  # Severe penalty for invalid data
        
        # 5. Improved difficulty balancing with progressive penalty
        for date, date_exams in exams_by_date.items():
            if len(date_exams) > 1:
                total_difficulty = sum(exam.difficulty for exam, _ in date_exams)
                avg_difficulty = total_difficulty / len(date_exams)
                
                # Apply penalty if average difficulty too high
                if avg_difficulty > 3.5:
                    penalty += DIFFICULTY_WEIGHT * (avg_difficulty - 3.5) ** 2 * len(date_exams)
                
                # Apply higher penalty if total difficulty too high
                if total_difficulty > 15:
                    penalty += DIFFICULTY_WEIGHT * (total_difficulty - 15)
        
        # 6. Check for good exam spread (bonus)
        if exams_by_date:
            num_days_used = len(exams_by_date)
            total_possible_days = len(set(ts.date_str for ts in self.time_slots))
            spread_ratio = num_days_used / total_possible_days
            
            # Give bonus for using more days (better spread)
            if spread_ratio > 0.7:
                penalty += SPREAD_BONUS * int(spread_ratio * 10)
        
        # Store conflict statistics
        self.conflict_stats = {
            'student_conflicts': len(self.student_conflicts),
            'room_conflicts': len(self.room_conflicts),
            'consecutive_exams': len(self.consecutive_exams),
            'capacity_issues': len(self.capacity_issues),
            'non_consecutive_slots': len(self.non_consecutive_slots)
        }
        
        return -penalty  # Higher is better
    
    def print_conflict_report(self):
        """Print detailed information about conflicts in the schedule"""
        print("\n====== CONFLICT REPORT ======")
        print(f"Total Student Conflicts: {len(self.student_conflicts)}")
        print(f"Total Room Conflicts: {len(self.room_conflicts)}")
        print(f"Total Capacity Issues: {len(self.capacity_issues)}")
        print(f"Students with Multiple Exams per Day: {len(self.consecutive_exams)}")
        print(f"Non-consecutive Timeslot Issues: {len(self.non_consecutive_slots)}")
        
        # Print all student conflicts
        if self.student_conflicts:
            print("\n----- STUDENT CONFLICTS -----")
            for i, (student_id, date, timeslot_id, exam1, exam2) in enumerate(self.student_conflicts[:10], 1):
                print(f"{i}. Student {student_id} has conflicting exams {exam1} and {exam2} on {date} at timeslot {timeslot_id}")
            
            if len(self.student_conflicts) > 10:
                print(f"... and {len(self.student_conflicts) - 10} more conflicts")
                
            # Count conflicts per student
            student_conflict_count = {}
            for student_id, _, _, _, _ in self.student_conflicts:
                student_conflict_count[student_id] = student_conflict_count.get(student_id, 0) + 1
            
            # Print students with most conflicts
            most_conflicted = sorted(student_conflict_count.items(), key=lambda x: x[1], reverse=True)[:5]
            if most_conflicted:
                print("\nStudents with most conflicts:")
                for student_id, count in most_conflicted:
                    print(f"Student {student_id}: {count} conflicts")
        
        # Print room conflicts
        if self.room_conflicts:
            print("\n----- ROOM CONFLICTS -----")
            for i, (room_id, date, timeslot_id, exam1, exam2) in enumerate(self.room_conflicts[:10], 1):
                print(f"{i}. Room {room_id} double-booked for exams {exam1} and {exam2} on {date} at timeslot {timeslot_id}")
            
            if len(self.room_conflicts) > 10:
                print(f"... and {len(self.room_conflicts) - 10} more room conflicts")
        
        # Print capacity issues
        if self.capacity_issues:
            print("\n----- CAPACITY ISSUES -----")
            for i, (exam_id, needed, available) in enumerate(self.capacity_issues[:10], 1):
                deficit = needed - available
                print(f"{i}. Exam {exam_id} needs {needed} seats but only {available} available (deficit: {deficit})")
            
            if len(self.capacity_issues) > 10:
                print(f"... and {len(self.capacity_issues) - 10} more capacity issues")
        
        # Print students with multiple exams in a day
        if self.consecutive_exams:
            print("\n----- MULTIPLE EXAMS PER DAY -----")
            for i, (student_id, date, exams) in enumerate(self.consecutive_exams[:10], 1):
                print(f"{i}. Student {student_id} has {len(exams)} exams on {date}: {', '.join(map(str, exams))}")
            
            if len(self.consecutive_exams) > 10:
                print(f"... and {len(self.consecutive_exams) - 10} more students with multiple exams per day")
        
        print("\n==============================")

