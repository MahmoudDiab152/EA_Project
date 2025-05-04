from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import io

def generate_pdf_timetable(timetable, exams, rooms, filename="exam_schedule.pdf", conflict_data=None):
    """Generate a stylish PDF timetable with exam schedule and statistics."""
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    
    # Set up styles
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading1"]
    normal_style = styles["Normal"]
    
    # Create custom styles
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.darkblue,
        spaceAfter=12
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.darkblue,
        spaceAfter=6
    )
    
    alert_style = ParagraphStyle(
        'Alert',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.red,
        spaceAfter=6
    )
    
    # Add title and date
    elements.append(Paragraph("Examination Schedule", title_style))
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", normal_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add summary section
    elements.append(Paragraph("Summary", section_style))
    
    # Calculate summary statistics
    all_students = set()
    for exam in exams:
        for student in exam.students:
            all_students.add(student.student_id)
    
    # Find date range of exam period
    all_dates = []
    for exam_id, (_, slots) in timetable.schedule.items():
        for slot in slots:
            all_dates.append(slot.date_str)
    
    exam_period = f"{min(all_dates, default='N/A')} to {max(all_dates, default='N/A')}"
    
    # Summary data
    summary_data = [
        ["Total Exams:", f"{len(exams)}"],
        ["Total Students:", f"{len(all_students)}"],
        ["Total Rooms:", f"{len(rooms)}"],
        ["Exam Period:", exam_period]
    ]
    
    # Add conflict summary if available
    if conflict_data and 'conflict_stats' in conflict_data:
        stats = conflict_data['conflict_stats']
        summary_data.extend([
            ["Student Conflicts:", f"{stats.get('student_conflicts', 0)}"],
            ["Room Conflicts:", f"{stats.get('room_conflicts', 0)}"],
            ["Capacity Issues:", f"{stats.get('capacity_issues', 0)}"],
            
        ])
    
    # Create summary table
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Generate visualizations if conflict data is available
    
    
    # Daily Exam Schedule
    elements.append(Paragraph("Daily Exam Schedule", section_style))
    
    # Organize schedule by date
    schedule_by_date = defaultdict(list)
    for exam_id, (assigned_rooms, timeslots) in timetable.schedule.items():
        # Find the corresponding exam object
        exam = next((e for e in exams if e.exam_id == exam_id), None)
        if not exam:
            continue
            
        # For each date this exam occurs
        for timeslot in timeslots:
            date_str = timeslot.date_str
            
            # Format rooms as a string
            room_str = ", ".join(f"{r.room_id}" for r in assigned_rooms)
            
            schedule_by_date[date_str].append({
                'exam_id': exam_id,
                'course_name': getattr(exam, 'course_name', f"Exam {exam_id}"),
                'timeslot': timeslot.timeslot_id,
                'timeslot_str': f"{timeslot.start_time}-{timeslot.end_time}",
                'rooms': room_str,
                'students': len(exam.students)
            })
    
    # Sort dates
    sorted_dates = sorted(schedule_by_date.keys())
    
    # Create a schedule table for each date
    for date in sorted_dates:
        # Add date header
        elements.append(Paragraph(f"Date: {date}", subtitle_style))
        
        # Sort exams by timeslot for this date
        exams_on_date = sorted(schedule_by_date[date], key=lambda x: x['timeslot'])
        
        # Table header
        table_data = [['Exam ID', 'Course', 'Time', 'Rooms', 'Students']]
        
        # Add exam data to table
        for exam_info in exams_on_date:
            table_data.append([
                exam_info['exam_id'],
                exam_info['course_name'],
                exam_info['timeslot_str'],
                exam_info['rooms'],
                exam_info['students']
            ])
        
        # Create and style the table
        schedule_table = Table(table_data, colWidths=[0.8*inch, 2*inch, 1.2*inch, 1.5*inch, 0.8*inch])
        schedule_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lavender),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (-1, 1), (-1, -1), 'CENTER'),
        ]))
        
        elements.append(schedule_table)
        elements.append(Spacer(1, 0.2*inch))
    
    # Add detailed conflict report if available
    if conflict_data:
        elements.append(PageBreak())
        elements.append(Paragraph("Detailed Conflict Report", section_style))
        
        # Student Conflicts
        if conflict_data.get('student_conflicts'):
            elements.append(Paragraph("Student Conflicts", subtitle_style))
            
            # Table header
            student_conflict_data = [['Student ID', 'Date', 'Timeslot', 'Exam 1', 'Exam 2']]
            
            # Add conflicts (limit to first 20)
            for i, (student_id, date, timeslot_id, exam1, exam2) in enumerate(conflict_data['student_conflicts'][:20]):
                student_conflict_data.append([
                    str(student_id),
                    date,
                    str(timeslot_id),
                    str(exam1),
                    str(exam2)
                ])
            
            # Add note if there are more conflicts
            if len(conflict_data['student_conflicts']) > 20:
                remaining = len(conflict_data['student_conflicts']) - 20
                elements.append(Paragraph(f"Showing 20 of {len(conflict_data['student_conflicts'])} student conflicts", 
                                         alert_style))
            
            # Create table
            if len(student_conflict_data) > 1:  # Only if we have data rows
                conflict_table = Table(student_conflict_data, colWidths=[1*inch, 1.2*inch, 1*inch, 1*inch, 1*inch])
                conflict_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.pink),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ]))
                elements.append(conflict_table)
                elements.append(Spacer(1, 0.2*inch))
        
        # Room Conflicts
        if conflict_data.get('room_conflicts'):
            elements.append(Paragraph("Room Conflicts", subtitle_style))
            
            # Table header
            room_conflict_data = [['Room ID', 'Date', 'Timeslot', 'Exam 1', 'Exam 2']]
            
            # Add conflicts (limit to first 20)
            for i, (room_id, date, timeslot_id, exam1, exam2) in enumerate(conflict_data['room_conflicts'][:20]):
                room_conflict_data.append([
                    str(room_id),
                    date,
                    str(timeslot_id),
                    str(exam1),
                    str(exam2)
                ])
            
            # Add note if there are more conflicts
            if len(conflict_data['room_conflicts']) > 20:
                remaining = len(conflict_data['room_conflicts']) - 20
                elements.append(Paragraph(f"Showing 20 of {len(conflict_data['room_conflicts'])} room conflicts", 
                                         alert_style))
            
            # Create table
            if len(room_conflict_data) > 1:  # Only if we have data rows
                conflict_table = Table(room_conflict_data, colWidths=[1*inch, 1.2*inch, 1*inch, 1*inch, 1*inch])
                conflict_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.pink),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ]))
                elements.append(conflict_table)
                elements.append(Spacer(1, 0.2*inch))
        
        # Capacity Issues
        if conflict_data.get('capacity_issues'):
            elements.append(Paragraph("Capacity Issues", subtitle_style))
            
            # Table header
            capacity_data = [['Exam ID', 'Students', 'Available Seats', 'Deficit']]
            
            # Add capacity issues (limit to first 20)
            for i, (exam_id, needed, available) in enumerate(conflict_data['capacity_issues'][:20]):
                deficit = needed - available
                capacity_data.append([
                    str(exam_id),
                    str(needed),
                    str(available),
                    str(deficit)
                ])
            
            # Add note if there are more issues
            if len(conflict_data['capacity_issues']) > 20:
                remaining = len(conflict_data['capacity_issues']) - 20
                elements.append(Paragraph(f"Showing 20 of {len(conflict_data['capacity_issues'])} capacity issues", 
                                         alert_style))
            
            # Create table
            if len(capacity_data) > 1:  # Only if we have data rows
                capacity_table = Table(capacity_data, colWidths=[1*inch, 1.2*inch, 1.5*inch, 1*inch])
                capacity_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.pink),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ]))
                elements.append(capacity_table)
                elements.append(Spacer(1, 0.2*inch))
        
        # Multiple Exams Per Day
        if conflict_data.get('consecutive_exams'):
            elements.append(Paragraph("Students with Multiple Exams in a Day", subtitle_style))
            
            # Table header
            consecutive_data = [['Student ID', 'Date', 'Number of Exams', 'Exam IDs']]
            
            # Add consecutive exam issues (limit to first 20)
            for i, (student_id, date, exams) in enumerate(conflict_data['consecutive_exams'][:20]):
                consecutive_data.append([
                    str(student_id),
                    date,
                    str(len(exams)),
                    ", ".join(map(str, exams))
                ])
            
            # Add note if there are more issues
            if len(conflict_data['consecutive_exams']) > 20:
                remaining = len(conflict_data['consecutive_exams']) - 20
                elements.append(Paragraph(f"Showing 20 of {len(conflict_data['consecutive_exams'])} students with multiple exams", 
                                         alert_style))
            
            # Create table
            if len(consecutive_data) > 1:  # Only if we have data rows
                consecutive_table = Table(consecutive_data, colWidths=[1*inch, 1.2*inch, 1.2*inch, 2*inch])
                consecutive_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.pink),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                    ('ALIGN', (3, 1), (3, -1), 'LEFT'),
                ]))
                elements.append(consecutive_table)
        
        # Non-consecutive Timeslots
        if conflict_data.get('non_consecutive_slots'):
            elements.append(Paragraph("Non-consecutive Timeslot Issues", subtitle_style))
            
            # Table header
            nonconsec_data = [['Exam ID', 'Timeslot IDs']]
            
            # Add non-consecutive issues (limit to first 20)
            for i, (exam_id, timeslot_ids) in enumerate(conflict_data['non_consecutive_slots'][:20]):
                nonconsec_data.append([
                    str(exam_id),
                    ", ".join(map(str, timeslot_ids))
                ])
            
            # Add note if there are more issues
            if len(conflict_data['non_consecutive_slots']) > 20:
                remaining = len(conflict_data['non_consecutive_slots']) - 20
                elements.append(Paragraph(f"Showing 20 of {len(conflict_data['non_consecutive_slots'])} non-consecutive slot issues", 
                                         alert_style))
            
            # Create table
            if len(nonconsec_data) > 1:  # Only if we have data rows
                nonconsec_table = Table(nonconsec_data, colWidths=[1.5*inch, 4*inch])
                nonconsec_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.pink),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ]))
                elements.append(nonconsec_table)
     
    # Generate the PDF
    doc.build(elements)
    print(f"Timetable PDF generated successfully: {filename}")
    
    return filename

def visualize_comparison(results):
    """Create visualizations comparing ACO and GA performance"""
    # Set up the figure with subplots
    fig = plt.figure(figsize=(15, 12))
    fig.suptitle('ACO vs GA Algorithm Comparison for Exam Timetabling', fontsize=16)
    
    # 1. Execution Time Comparison
    ax1 = fig.add_subplot(2, 2, 1)
    algorithms = ['ACO', 'GA']
    times = [results['aco']['execution_time'], results['ga']['execution_time']]
    
    ax1.bar(algorithms, times, color=['#3498db', '#e74c3c'])
    ax1.set_title('Execution Time Comparison')
    ax1.set_ylabel('Time (seconds)')
    for i, v in enumerate(times):
        ax1.text(i, v + 0.1, f"{v:.2f}s", ha='center')
    
    # 2. Fitness Comparison
    ax2 = fig.add_subplot(2, 2, 2)
    # Convert fitness values to positive for easier visualization
    fitness_values = [abs(results['aco']['fitness']), abs(results['ga']['fitness'])]
    
    ax2.bar(algorithms, fitness_values, color=['#3498db', '#e74c3c'])
    ax2.set_title('Fitness Comparison (Lower is Better)')
    ax2.set_ylabel('Penalty Points')
    for i, v in enumerate(fitness_values):
        ax2.text(i, v + 5, f"{v:.0f}", ha='center')
    
    # 3. Conflict Comparison
    ax3 = fig.add_subplot(2, 1, 2)
    conflict_types = ['Student\nConflicts', 'Room\nConflicts', 'Capacity\nIssues', 
                      'Multiple Exams\nPer Day', 'Non-consecutive\nTimeslots']
    
    aco_conflicts = [
        results['aco']['conflicts']['student_conflicts'],
        results['aco']['conflicts']['room_conflicts'],
        results['aco']['conflicts']['capacity_issues'],
        results['aco']['conflicts']['consecutive_exams'],
        results['aco']['conflicts']['non_consecutive_slots']
    ]
    
    ga_conflicts = [
        results['ga']['conflicts']['student_conflicts'],
        results['ga']['conflicts']['room_conflicts'],
        results['ga']['conflicts']['capacity_issues'],
        results['ga']['conflicts']['consecutive_exams'],
        results['ga']['conflicts']['non_consecutive_slots']
    ]
    
    x = np.arange(len(conflict_types))
    width = 0.35
    
    rects1 = ax3.bar(x - width/2, aco_conflicts, width, label='ACO', color='#3498db')
    rects2 = ax3.bar(x + width/2, ga_conflicts, width, label='GA', color='#e74c3c')
    
    ax3.set_title('Conflict Comparison')
    ax3.set_ylabel('Number of Conflicts')
    ax3.set_xticks(x)
    ax3.set_xticklabels(conflict_types)
    ax3.legend()
    
    # Add labels to the bars
    for rect in rects1:
        height = rect.get_height()
        ax3.annotate(f'{height}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')
    
    for rect in rects2:
        height = rect.get_height()
        ax3.annotate(f'{height}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig('algorithm_comparison.png', dpi=300)
    plt.savefig('algorithm_comparison.pdf')
    plt.show()
