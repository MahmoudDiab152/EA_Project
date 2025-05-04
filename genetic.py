import random
from datetime import datetime
from Time_Slots import generate_timeslots, timeslots
from encoder import create_encoded_lists, decode_individual
from data import Data
import room

class GeneticAlgorithm:
    def __init__(self):
        # Read data for decoding/encoding
        self.students = Data.read_students()
        self.exams = Data.read_exams(self.students)
        self.rooms = Data.read_rooms()
        self.time_slots = timeslots
        
        # Create encoded lists for mutation
        self.encoded_courses, self.encoded_time_slots, self.encoded_halls = create_encoded_lists(
            self.exams, self.time_slots, self.rooms
        )
    
    def genetic_algorithm(self, population, max_generation, optimalFitness, mutation_rate=0.1):
        best_individual = None
        best_fitness = float('-inf')
        best_decoded = None
        
        for generation in range(max_generation):
            # Evaluate fitness for each individual
            fitness_scores = []
            for individual in population:
                # Decode individual for fitness evaluation
                decoded = decode_individual(individual, self.rooms, self.time_slots, self.exams)
                fitness = self.get_fitness(decoded, self.exams)
                fitness_scores.append(fitness)
            
            # Track best individual
            current_best = max(fitness_scores)
            current_best_idx = fitness_scores.index(current_best)
            
            if current_best > best_fitness:
                best_fitness = current_best
                best_individual = population[current_best_idx]
                best_decoded = decode_individual(best_individual, self.rooms, self.time_slots, self.exams)
                # Get conflicts of best individual
                self.get_fitness(best_decoded, self.exams)
            
            # Print generation info
            print(f"Generation {generation}: Best Fitness = {current_best}")
                
            # Early termination if optimal fitness reached
            if best_fitness >= optimalFitness:
                break
            
            # Create new generation
            new_population = []
            while len(new_population) < len(population):
                # Selection
                parent1 = self.tournament_selection(population, fitness_scores, tournament_size=3)
                parent2 = self.tournament_selection(population, fitness_scores, tournament_size=3)
                
                # Crossover
                child1, child2 = self.two_point_crossover_timetable(parent1, parent2)
                
                # Mutation
                if random.random() < mutation_rate:
                    child1 = self.mutate_timetable(child1)
                if random.random() < mutation_rate:
                    child2 = self.mutate_timetable(child2)
                
                new_population.extend([child1, child2])
            
            # Ensure population size remains consistent
            population = new_population[:len(population)]
        
        # Print final generation info
        print(f"Final Best Fitness: {best_fitness} at generation {generation}")
        
        # Run fitness one last time on best individual to ensure conflict data is current
        best_decoded = decode_individual(best_individual, self.rooms, self.time_slots, self.exams)
        _ = self.get_fitness(best_decoded, self.exams)
        
        # Print conflict statistics
        self.print_conflict_report()
        
        return best_individual, generation, best_decoded
    
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
        
        return self.conflict_stats

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
        STUDENT_CONFLICT_WEIGHT = 70  # Direct student conflict (increased from 50)
        CONSECUTIVE_EXAMS_WEIGHT = 25  # Consecutive exams on same day (increased from 15)
        TIMESLOT_CONSISTENCY_WEIGHT = 50  # Non-consecutive timeslots
        DIFFICULTY_WEIGHT = 3      # Weight for difficulty balancing (increased from 2)
        
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

    def mutate_timetable(self, individual):
        mutated = individual.copy()
        if not mutated:
            return mutated
            
        # Pick a random assignment to mutate
        index = random.randint(0, len(mutated) - 1)
        
        # Parse the assignment
        parts = mutated[index].split('-')
        if len(parts) != 3:
            return mutated
            
        exam_code = parts[0]
        timeslot_parts = parts[1].split('+')
        room_parts = parts[2].split('+')
        
        # Choose what to mutate: timeslots, rooms, or both
        mutation_type = random.choice(["timeslots", "rooms", "both"])
        
        if mutation_type in ["timeslots", "both"]:
            timeslot_action = random.choice(["add", "remove", "shift"]) if len(timeslot_parts) > 1 else random.choice(["add", "shift"])
            
            if timeslot_action == "add" and len(timeslot_parts) < 3:  # Limit to 3 slots max
                # Find the highest timeslot ID
                highest_id = max([int(ts[2:]) for ts in timeslot_parts])
                new_ts = f"TS{highest_id + 1}"
                timeslot_parts.append(new_ts)
                
            elif timeslot_action == "remove" and len(timeslot_parts) > 1:
                # Remove a random timeslot
                timeslot_to_remove = random.choice(timeslot_parts)
                timeslot_parts.remove(timeslot_to_remove)
                
            elif timeslot_action == "shift":
                # Shift all timeslots by +1 or -1
                shift = random.choice([-1, 1])
                max_timeslot_id = len(self.time_slots)
                
                new_timeslot_parts = []
                for ts in timeslot_parts:
                    current_id = int(ts[2:])
                    new_id = current_id + shift
                    
                    # Ensure ID stays within bounds
                    if 1 <= new_id <= max_timeslot_id:
                        new_timeslot_parts.append(f"TS{new_id}")
                    else:
                        new_timeslot_parts.append(ts)  # Keep original if out of bounds
                        
                timeslot_parts = new_timeslot_parts
        
        if mutation_type in ["rooms", "both"]:
            
            room_action = random.choice(["add", "remove", "replace"]) if len(room_parts) > 1 else random.choice(["add", "replace"])
            
            if room_action == "add":
                # Add a random room
                new_room = f"R{random.randint(1, len(self.rooms))}"
                if new_room not in room_parts:
                    room_parts.append(new_room)
                    
            elif room_action == "remove" and len(room_parts) > 1:
                # Remove a random room
                room_to_remove = random.choice(room_parts)
                room_parts.remove(room_to_remove)
                
            elif room_action == "replace":
                # Replace a random room
                if room_parts:
                    index_to_replace = random.randint(0, len(room_parts) - 1)
                    room_parts[index_to_replace] = f"R{random.randint(1, len(self.rooms))}"
        
        # Reconstruct the mutated assignment
        new_timeslots_str = "+".join(timeslot_parts)
        new_rooms_str = "+".join(room_parts)
        mutated[index] = f"{exam_code}-{new_timeslots_str}-{new_rooms_str}"
        
        return mutated

    def two_point_crossover_timetable(self, parent1, parent2):
        # Ensure parents have at least 2 exams for meaningful crossover
        if len(parent1) < 2 or len(parent2) < 2:
            return parent1, parent2
        
        # Make sure crossover points are within valid range
        min_length = min(len(parent1), len(parent2))
        
        # Select first crossover point (avoiding first and last positions)
        crossover_point1 = random.randint(1, min_length - 2)
        
        # Select second crossover point after the first one
        crossover_point2 = random.randint(crossover_point1 + 1, min_length - 1)
        
        # Create children by swapping middle segments
        child1 = parent1[:crossover_point1] + parent2[crossover_point1:crossover_point2] + parent1[crossover_point2:]
        child2 = parent2[:crossover_point1] + parent1[crossover_point1:crossover_point2] + parent2[crossover_point2:]
        
        return child1, child2

    def tournament_selection(self, population, fitness_scores, tournament_size):
        # Select a random subset of individuals for the tournament
        tournament_indices = random.sample(range(len(population)), tournament_size)
        
        # Find the best individual in the tournament
        best = tournament_indices[0]
        for index in tournament_indices:
            if fitness_scores[index] > fitness_scores[best]:  # Changed comparison to > since higher fitness is better
                best = index
                
        return population[best]

    def get_consecutive_timeslots(self, required_slots):
        """Find consecutive timeslots on the same day"""
        if required_slots <= 1:
            return [random.choice(self.time_slots)]
        
        # Group timeslots by date
        timeslots_by_date = {}
        for ts in self.time_slots:
            if ts.date_str not in timeslots_by_date:
                timeslots_by_date[ts.date_str] = []
            timeslots_by_date[ts.date_str].append(ts)
        
        # Sort timeslots by ID for each date
        for date, slots in timeslots_by_date.items():
            timeslots_by_date[date] = sorted(slots, key=lambda ts: ts.timeslot_id)
        
        # Randomly select a date that has enough slots
        valid_dates = [date for date, slots in timeslots_by_date.items() 
                      if len(slots) >= required_slots]
        
        if not valid_dates:
            return [random.choice(self.time_slots)]  # Fallback if no valid dates
        
        selected_date = random.choice(valid_dates)
        slots = timeslots_by_date[selected_date]
        
        # Find a starting position that allows for consecutive slots
        max_start_idx = len(slots) - required_slots
        if max_start_idx < 0:
            return [random.choice(self.time_slots)]  # Fallback
        
        start_idx = random.randint(0, max_start_idx)
        return slots[start_idx:start_idx + required_slots]

    def generate_population(self, population_size=50):
        population = []
        
        for _ in range(population_size):
            individual = []
            for exam in self.exams:
                # Determine how many rooms this exam needs
                students_count = len(exam.students)
                available_rooms = sorted(self.rooms, key=lambda r: r.capacity, reverse=True)
                
                # Calculate how many time slots we need based on exam duration
                required_slots = max(1, exam.duration // 120)  # Assuming 2 hours per slot
                
                # Find consecutive time slots on the same day
                consecutive_slots = self.get_consecutive_timeslots(required_slots)
                
                # Assign rooms until we have enough capacity
                assigned_rooms = []
                remaining_students = students_count
                
                while remaining_students > 0 and available_rooms:
                    # Pick a random room from available rooms
                    room = random.choice(available_rooms)
                    available_rooms.remove(room)
                    
                    assigned_rooms.append(room)
                    remaining_students -= room.capacity
                    
                    if remaining_students <= 0 or not available_rooms:
                        break
                
                # Create assignment string with multiple rooms and timeslots
                room_str = "+".join([f"R{room.room_id}" for room in assigned_rooms])
                timeslot_str = "+".join([f"TS{ts.timeslot_id}" for ts in consecutive_slots])
                assignment = f"C{self.exams.index(exam)+1}-{timeslot_str}-{room_str}"
                individual.append(assignment)
            
            population.append(individual)
        
        return population

