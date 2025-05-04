from exam import ExamAssignment


def create_encoded_lists(exams, timeslots, rooms):
    """Create encoded lists for exams, timeslots, and rooms."""
    encoded_courses = [f"C{i+1}" for i in range(len(exams))]
    encoded_time_slots = [f"TS{i+1}" for i in range(len(timeslots))]
    encoded_halls = [f"R{i+1}" for i in range(len(rooms))]
    return encoded_courses, encoded_time_slots, encoded_halls

def decode_individual(encoded_individual, rooms, timeslots, exams):
    """Decode an encoded individual into a list of assignments."""
    decoded = []
    
    # Create mappings for faster lookup
    exam_map = {f"C{i+1}": exam for i, exam in enumerate(exams)}
    ts_map = {f"TS{i+1}": ts for i, ts in enumerate(timeslots)}
    room_map = {f"R{i+1}": room for i, room in enumerate(rooms)}
    
    for item in encoded_individual:
        try:
            # Parse format like "C1-TS1+TS2-R1+R2" (multiple timeslots and rooms)
            parts = item.split('-')
            if len(parts) == 3:
                exam_code, ts_codes, room_codes = parts
                exam = exam_map.get(exam_code)
                
                # Get all timeslots
                timeslot_list = []
                for ts_code in ts_codes.split('+'):
                    ts = ts_map.get(ts_code)
                    if ts:
                        timeslot_list.append(ts)
                
                # Get all rooms
                room_list = []
                for room_code in room_codes.split('+'):
                    room = room_map.get(room_code)
                    if room:
                        room_list.append(room)
                
                if exam and timeslot_list and room_list:
                    decoded.append({
                        'exam': exam,
                        'timeslots': timeslot_list,
                        'rooms': room_list
                    })
        except (ValueError, KeyError) as e:
            print(f"Decoding error for {item}: {str(e)}")
            continue
    
    return decoded

