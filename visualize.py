from matplotlib import pyplot as plt


def visualize_timetable(timetable, exams, timeslots, rooms):
    # Set style for a more professional look
    plt.style.use('ggplot')
    
    # Create figure with multiple subplots
    fig = plt.figure(figsize=(18, 12))
    
    # Create main grid spec
    gs = fig.add_gridspec(1, 5)
    
    # Main timetable plot
    ax_main = fig.add_subplot(gs[0, :4])
    
    # Right side information panels
    ax_rooms = fig.add_subplot(gs[0, 4:])
    
    # Get unique dates and time slots
    dates = sorted(set(timeslot.date_str for _, timeslot in timetable.schedule.values()))
    unique_times = sorted(set(timeslot.time_str for timeslot in timeslots))
    
    # Define colors for different exams
    exam_colors = plt.cm.tab20.colors
    
    # Number of rows (dates) and columns (time slots)
    n_rows = len(dates)
    n_cols = len(unique_times)
    
    # Create a grid for the timetable
    cell_height = 1.0
    cell_width = 1.0
    
    # Create a dictionary for the grid cells
    grid = {}
    for i, date in enumerate(dates):
        for j, time_str in enumerate(unique_times):
            grid[(date, time_str)] = []
    
    # Fill the grid with exams
    for exam_id, (room, timeslot) in timetable.schedule.items():
        exam = next(e for e in exams if e.exam_id == exam_id)
        grid[(timeslot.date_str, timeslot.time_str)].append((exam, room))
    
    # Plot the grid and exams in the main timetable
    for i, date in enumerate(dates):
        ax_main.text(-0.5, i * cell_height + cell_height/2, date, 
                ha='right', va='center', fontweight='bold')
        
        for j, time_str in enumerate(unique_times):
            # Draw cell borders
            rect = plt.Rectangle((j * cell_width, i * cell_height), 
                                cell_width, cell_height, 
                                fill=False, edgecolor='gray', linewidth=1)
            ax_main.add_patch(rect)
            
            # Draw time slot at the top
            if i == 0:
                ax_main.text(j * cell_width + cell_width/2, -0.2, 
                        f"{time_str}", 
                        ha='center', va='center', fontweight='bold')
            
            # Add exams to the cell
            exams_in_cell = grid[(date, time_str)]
            if exams_in_cell:
                # Sort exams by exam_id
                exams_in_cell.sort(key=lambda x: x[0].exam_id)
                
                # Draw each exam in the cell
                for k, (exam, room) in enumerate(exams_in_cell):
                    # Position each exam within the cell, stacked if multiple
                    y_offset = 0.1 + (k * 0.2) if len(exams_in_cell) > 1 else 0.25
                    
                    # Exam color based on exam_id
                    color_idx = (exam.exam_id - 1) % len(exam_colors)
                    
                    # Create the exam block
                    exam_rect = plt.Rectangle(
                        (j * cell_width + 0.1, i * cell_height + y_offset), 
                        cell_width - 0.2, 0.5 / len(exams_in_cell), 
                        facecolor=exam_colors[color_idx], 
                        alpha=0.7, 
                        edgecolor='black', 
                        linewidth=1
                    )
                    ax_main.add_patch(exam_rect)
                    
                    # Add exam info with student count instead of names
                    student_count = len(exam.students)
                    exam_text = f"{exam.course_name}\nRoom: {room.room_name}\nStudents: {student_count}"
                    
                    ax_main.text(
                        j * cell_width + cell_width/2, 
                        i * cell_height + y_offset + (0.25 / len(exams_in_cell)), 
                        exam_text, 
                        ha='center', 
                        va='center', 
                        fontsize=9,
                        fontweight='bold'
                    )
    
    # Set axis limits for main timetable
    ax_main.set_xlim(-0.5, n_cols * cell_width)
    ax_main.set_ylim(n_rows * cell_height, -0.5)
    
    # Remove axes for main timetable
    ax_main.axis('off')
    
    # Add title to main timetable
    ax_main.set_title("Exam Timetable: Time Slots × Days", fontsize=16, fontweight='bold', pad=20)
    
    # Right information panel - Rooms
    ax_rooms.axis('off')
    
    # Draw room information box
    room_box = plt.Rectangle((0, 0.55), 1, 0.4, fill=True, alpha=0.1, color='blue')
    ax_rooms.add_patch(room_box)
    ax_rooms.text(0.5, 0.95, "Room Information", ha='center', va='center', fontsize=12, fontweight='bold')
    
    # Add room details
    room_info = ""
    for i, room in enumerate(rooms):
        room_info += f"Room {room.room_name}: Capacity {room.capacity}\n"
    ax_rooms.text(0.5, 0.75, room_info, ha='center', va='center', fontsize=10)
    
    # Draw exam information box
    exam_box = plt.Rectangle((0, 0.05), 1, 0.4, fill=True, alpha=0.1, color='green')
    ax_rooms.add_patch(exam_box)
    ax_rooms.text(0.5, 0.45, "Exam Enrollment", ha='center', va='center', fontsize=12, fontweight='bold')
    
    # Add exam details
    exam_info = ""
    for exam in exams:
        exam_info += f"{exam.course_name}: {len(exam.students)} students\n"
    ax_rooms.text(0.5, 0.25, exam_info, ha='center', va='center', fontsize=10)
    
    # Set limits for the room info panel
    ax_rooms.set_xlim(0, 1)
    ax_rooms.set_ylim(0, 1)
    
    # Add legend for exams
    legend_elements = [
        plt.Rectangle((0,0), 1, 1, facecolor=exam_colors[i % len(exam_colors)], 
                     edgecolor='black', alpha=0.7)
        for i in range(len(exams))
    ]
    legend_labels = [f"{exam.course_name} (Difficulty: {exam.difficulty})" for exam in exams]
    ax_main.legend(legend_elements, legend_labels, 
             title="Exams", loc='upper center', 
             bbox_to_anchor=(0.5, -0.05), ncol=3)
    
    # Adjust layout
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.15)
    
    # Show the plot
    plt.show()
