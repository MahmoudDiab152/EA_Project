import time
import matplotlib.pyplot as plt
import numpy as np
from timetable import Timetable
from visualize import generate_pdf_timetable, visualize_comparison
from visualize_all_table import generate_entire_timetable
from aco import ACO
from genetic import GeneticAlgorithm

if __name__ == "__main__":
    results = {}
     # Run Genetic Algorithm
    print("\n[RUNNING] Genetic Algorithm...")
    ga_start_time = time.time()
    
    ga = GeneticAlgorithm()
    population = ga.generate_population(population_size=20)
    ga_solution, ga_generation, ga_decoded = ga.genetic_algorithm(
        population, 
        max_generation=100,
        optimalFitness=-50,  # Target fitness threshold
        mutation_rate=0.15
    )
    
    ga_end_time = time.time()
    ga_execution_time = ga_end_time - ga_start_time
    
    # Calculate GA fitness
    ga_fitness = ga.get_fitness(ga_decoded, ga.exams)
    
    # Get conflict stats
    ga_conflicts = ga.conflict_stats
    
    print(f"\n[COMPLETED] Genetic Algorithm")
    print(f"  - Execution time: {ga_execution_time:.2f} seconds")
    print(f"  - Best fitness: {ga_fitness}")
    print(f"  - Solution found at generation: {ga_generation}")
    
    # Create GA timetable
    ga_timetable = Timetable(ga_decoded)
    generate_entire_timetable(
        timetable=ga_timetable,
        exams=ga.exams,
        rooms=ga.rooms,
        filename="GA_Entire_Table.pdf"
    )
    generate_pdf_timetable(
        timetable=ga_timetable,
        exams=ga.exams,
        rooms=ga.rooms,
        filename="GA_Daily_Schedule.pdf",
        conflict_data={
            'student_conflicts': ga.student_conflicts,
            'room_conflicts': ga.room_conflicts,
            'capacity_issues': ga.capacity_issues,
            'consecutive_exams': ga.consecutive_exams,
            'non_consecutive_slots': ga.non_consecutive_slots,
            'conflict_stats': ga.conflict_stats
        }
    )
    
    # Store GA results
    results['ga'] = {
        'execution_time': ga_execution_time,
        'fitness': ga_fitness,
        'conflicts': ga_conflicts,
        'solution': ga_decoded
    }
    
    # Run ACO Algorithm
    print("\n[RUNNING] Ant Colony Optimization Algorithm...")
    aco_start_time = time.time()
    
    aco = ACO()
    aco_solution, aco_iteration, aco_decoded = aco.run_aco(
        num_iterations=2,
        num_ants=5,
        local_search_iterations=2
    )
    
    aco_end_time = time.time()
    aco_execution_time = aco_end_time - aco_start_time
    
    # Calculate ACO fitness
    aco_fitness = aco.get_fitness(aco_decoded, aco.exams)
    
    # Get conflict stats
    aco_conflicts = aco.conflict_stats
    
    print(f"\n[COMPLETED] ACO Algorithm")
    print(f"  - Execution time: {aco_execution_time:.2f} seconds")
    print(f"  - Best fitness: {aco_fitness}")
    print(f"  - Solution found at iteration: {aco_iteration}")
    
    # Create ACO timetable
    aco_timetable = Timetable(aco_decoded)
    generate_entire_timetable(
        timetable=aco_timetable,
        exams=aco.exams,
        rooms=aco.rooms,
        filename="ACO_Entire_Table.pdf"
    )
    generate_pdf_timetable(
        timetable=aco_timetable,
        exams=aco.exams,
        rooms=aco.rooms,
        filename="AC_Daily_Schedule.pdf",
        conflict_data={
            'student_conflicts': aco.student_conflicts,
            'room_conflicts': aco.room_conflicts,
            'capacity_issues': aco.capacity_issues,
            'consecutive_exams': aco.consecutive_exams,
            'non_consecutive_slots': aco.non_consecutive_slots,
            'conflict_stats': aco.conflict_stats
        }
    )
    
    # Store ACO results
    results['aco'] = {
        'execution_time': aco_execution_time,
        'fitness': aco_fitness,
        'conflicts': aco_conflicts,
        'solution': aco_decoded
    }
    
    print("\n" + "-" * 50)
    
    # Print comparison summary
    print("\n" + "=" * 50)
    print("ALGORITHM COMPARISON SUMMARY")
    print("=" * 50)
    
    print(f"\nExecution Time:")
    print(f"  - ACO: {aco_execution_time:.2f} seconds")
    print(f"  - GA:  {ga_execution_time:.2f} seconds")
    print(f"  - Time Difference: {abs(aco_execution_time - ga_execution_time):.2f} seconds")
    print(f"  - Faster Algorithm: {'ACO' if aco_execution_time < ga_execution_time else 'GA'}")
    
    print(f"\nSolution Quality:")
    print(f"  - ACO Fitness: {aco_fitness}")
    print(f"  - GA Fitness:  {ga_fitness}")
    print(f"  - Better Solution: {'ACO' if aco_fitness > ga_fitness else 'GA'}")
    
    print(f"\nConflict Comparison:")
    print(f"  - Student Conflicts: ACO: {aco_conflicts['student_conflicts']}, GA: {ga_conflicts['student_conflicts']}")
    print(f"  - Room Conflicts: ACO: {aco_conflicts['room_conflicts']}, GA: {ga_conflicts['room_conflicts']}")
    print(f"  - Capacity Issues: ACO: {aco_conflicts['capacity_issues']}, GA: {ga_conflicts['capacity_issues']}")
    print(f"  - Multiple Exams Per Day: ACO: {aco_conflicts['consecutive_exams']}, GA: {ga_conflicts['consecutive_exams']}")
    print(f"  - Non-consecutive Timeslots: ACO: {aco_conflicts['non_consecutive_slots']}, GA: {ga_conflicts['non_consecutive_slots']}")
    visualize_comparison(results)
    