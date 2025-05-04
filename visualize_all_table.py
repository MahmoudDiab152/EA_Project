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

def generate_entire_timetable(timetable, exams, rooms, filename="exam_schedule.pdf"):
    """Generate a stylish PDF timetable with exam schedule and statistics."""
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    
    # Set up styles
    styles = getSampleStyleStyles()
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
    
    # Add title and date
    elements.append(Paragraph("Examination Schedule", title_style))
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", normal_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add summary section
    elements.append(Paragraph("Summary", section_style))
    
    summary_data = [
        ["Total Exams Scheduled:", str(len(timetable.schedule))],
        ["Total Students:", str(len({student for exam in exams for student in exam.students}))],
        ["Exam Period:", f"{min(slot.date_str for exam_id, (_, slots) in timetable.schedule.items() for slot in slots)} to {max(slot.date_str for exam_id, (_, slots) in timetable.schedule.items() for slot in slots)}"],
        ["Total Rooms Used:", str(len(set(room.room_id for _, (rooms, _) in timetable.schedule.items() for room in rooms)))]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (1, 0), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Add main schedule
    elements.append(Paragraph("Exam Schedule", section_style))
    
    # Sort by date and time
    sorted_assignments = sorted(timetable.schedule.items(),
                              key=lambda x: (x[1][1][0].date, x[1][1][0].start_time))
    
    # Create the data for the table
    schedule_data = [
        ["Date", "Time", "Course", "Rooms", "Students", "Duration"]
    ]
    
    for exam_id, (assigned_rooms, timeslots) in sorted_assignments:
        exam = next(e for e in exams if e.exam_id == exam_id)
        room_names = ", ".join(room.room_name for room in assigned_rooms)
        
        
        # Handle multi-line room names if too long
        if len(room_names) > 30:
            room_parts = room_names.split(", ")
            room_names = ""
            line = ""
            for part in room_parts:
                if len(line) + len(part) + 2 <= 30:
                    if line:
                        line += ", " + part
                    else:
                        line = part
                else:
                    room_names += line + ",\n"
                    line = part
            room_names += line
                
        timeslot_str = f"{timeslots[0].time_str}"
        if len(timeslots) > 1:
            timeslot_str += f" to {timeslots[-1].time_str}"
        
        # Calculate duration in hours
        duration = len(timeslots) * 2  # Assuming 2 hours per timeslot
        
        schedule_data.append([
            timeslots[0].date_str,
            timeslot_str,
            exam.course_name,
            room_names,
            str(len(exam.students)),
            f"{duration} hours"
        ])
    
    # Create the main schedule table
    schedule_table = Table(
        schedule_data, 
        colWidths=[0.9*inch, 1.1*inch, 1.5*inch, 2.7*inch, 0.8*inch, 1*inch],
        repeatRows=1
    )
    
    # Add style to the table
    schedule_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        
        # Data rows - alternate colors
        ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
        ('BACKGROUND', (0, 3), (-1, 3), colors.lightgrey),
        ('BACKGROUND', (0, 5), (-1, 5), colors.lightgrey),
        ('BACKGROUND', (0, 7), (-1, 7), colors.lightgrey),
        ('BACKGROUND', (0, 9), (-1, 9), colors.lightgrey),
        ('BACKGROUND', (0, 11), (-1, 11), colors.lightgrey),
        ('BACKGROUND', (0, 13), (-1, 13), colors.lightgrey),
        ('BACKGROUND', (0, 15), (-1, 15), colors.lightgrey),
        ('BACKGROUND', (0, 17), (-1, 17), colors.lightgrey),
        ('BACKGROUND', (0, 19), (-1, 19), colors.lightgrey),
        ('BACKGROUND', (0, 21), (-1, 21), colors.lightgrey),
        
        # All cells
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        
        # Center specific columns
        ('ALIGN', (4, 1), (5, -1), 'CENTER'),
    ]))
    
    elements.append(schedule_table)
    elements.append(PageBreak())
    # Room utilization data
    elements.append(Paragraph("Room Utilization", subtitle_style))
    
    room_usage = defaultdict(int)
    for _, (assigned_rooms, _) in timetable.schedule.items():
        for room in assigned_rooms:
            room_usage[room.room_name] += 1
    
    # Sort rooms by usage
    top_rooms = sorted(room_usage.items(), key=lambda x: x[1], reverse=True)[:10]
    
    room_data = [["Room", "Number of Exams"]]
    room_data.extend(top_rooms)
    
    room_table = Table(room_data, colWidths=[4*inch, 2*inch])
    room_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        
        # Data rows
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        
        # Alternate row colors
        ('BACKGROUND', (0, 1), (-1, 1), colors.lightgrey),
        ('BACKGROUND', (0, 3), (-1, 3), colors.lightgrey),
        ('BACKGROUND', (0, 5), (-1, 5), colors.lightgrey),
        ('BACKGROUND', (0, 7), (-1, 7), colors.lightgrey),
        ('BACKGROUND', (0, 9), (-1, 9), colors.lightgrey),
    ]))
    
    elements.append(room_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Generate the PDF
    doc.build(elements)
    print(f"PDF timetable generated: {filename}")
    
    return filename

def getSampleStyleStyles():
    """Create a dictionary of styles for the document."""
    styles = getSampleStyleSheet()
    
    # Customize the Title style
    styles["Title"].textColor = colors.darkblue
    styles["Title"].fontSize = 20
    styles["Title"].spaceAfter = 12
    
    # Customize the Heading1 style
    styles["Heading1"].textColor = colors.darkblue
    styles["Heading1"].fontSize = 16
    styles["Heading1"].spaceAfter = 10
    
    # Customize the Normal style
    styles["Normal"].fontSize = 10
    styles["Normal"].spaceAfter = 6
    
    return styles

    """Generate charts for exam analytics."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # Prepare x-axis labels (dates)
    x = np.arange(len(dates))
    
    # Plot exams per day
    bars1 = ax1.bar(x, exam_counts, color='steelblue', width=0.6)
    ax1.set_ylabel('Number of Exams')
    ax1.set_title('Exams per Day')
    ax1.set_xticks(x)
    ax1.set_xticklabels(dates, rotation=45, ha='right')
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                 f'{int(height)}', ha='center', va='bottom')
    
    # Plot students per day
    bars2 = ax2.bar(x, student_counts, color='darkgreen', width=0.6)
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Number of Students')
    ax2.set_title('Students per Day')
    ax2.set_xticks(x)
    ax2.set_xticklabels(dates, rotation=45, ha='right')
    
    # Add value labels on bars
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 5,
                 f'{int(height)}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    
    return output_path