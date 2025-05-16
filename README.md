# Exam Timetabling Optimization Using GA & ACO

## Overview

This project solves the **Exam Timetabling Problem (ETP)** using two metaheuristic algorithms:
- Genetic Algorithm (GA)
- Ant Colony Optimization (ACO)

The aim is to generate conflict-free and well-optimized exam schedules while respecting both hard and soft constraints in an academic environment.

## Problem Definition

### Hard Constraints:
- No student can attend two exams simultaneously.
- Room capacity must not be exceeded.
- Rooms can't be double-booked.
- Multi-slot exams must use consecutive timeslots.

### Soft Constraints:
- Avoid multiple exams for a student on the same day.
- Even distribution of difficult exams.
- Minimize weekend scheduling.
- Spread exams uniformly across the schedule.

## Objectives
- Minimize student conflicts.
- Maximize room and timeslot utilization.
- Distribute exams uniformly.
- Minimize back-to-back exams for students.

## Genetic Algorithm (GA)

### Components:
- Chromosome: Encodes exam assignments to timeslots and rooms.
- Fitness Function: Penalizes violations and rewards well-optimized schedules.
- Operators:
  - Tournament selection
  - One-point and two-point crossover
  - Timeslot and room mutation

### Performance:
- Execution Time: ~64s
- Best Fitness Score: 27.0
- Convergence: Steady across generations

## Ant Colony Optimization (ACO)

### Components:
- Ants build solutions using pheromone trails.
- Probabilistic path selection based on pheromones and heuristics.
- Local Search: Post-construction adjustments to improve quality.

### Performance:
- Execution Time: ~3521s
- Best Fitness Score: 40
- Convergence: Unstable; early peak followed by degradation

## GA vs ACO Comparison

| Metric | GA | ACO | Winner |
|--------|----|-----|--------|
| Execution Time | 64.13s | 3521.42s | GA |
| Fitness Score (Lower is Better) | 27.0 | 40 | GA |
| Conflict Handling | 0 Conflicts | 0 Conflicts | Tie |
| Convergence | Steady | Degraded | GA |

**Final Verdict:** GA outperformed ACO in speed, solution quality, and stability.

## Tools & Libraries

- Python
- numpy
- random
- collections
- matplotlib
- reportlab
- datetime
- os

## Output

- PDF-formatted final timetable
- Conflict reports
- Optional visualizations via console and plots

## Solution Encoding

- Encoded Format: `C1-TS1+TS2-R1+R2` (for algorithm processing)
- Decoded Format: Python object representation (for constraint checking and analysis)

