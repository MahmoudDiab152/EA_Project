import csv
from exam import Exam
from room import Room
from student import Student

class Data:
  @staticmethod
  def read_students():
    students = []
    with open('students.csv', mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            students.append(Student(int(row['id']), row['name']))
    return students
  @staticmethod
  def read_rooms():
      rooms = []
      with open('rooms.csv', mode='r') as file:
          reader = csv.DictReader(file)
          for row in reader:
              rooms.append(Room(int(row['id']), row['room_name'], int(row['capacity'])))
      return rooms
  @staticmethod
  def read_exams(students):
      exams = []
      student_dict = {student.student_id: student for student in students}
      with open('exams.csv', mode='r') as file:
          reader = csv.DictReader(file)
          for row in reader:
              student_ids = list(map(int, row['student_ids'].split(';')))
              exam_students = [student_dict[sid] for sid in student_ids]
              exams.append(Exam(int(row['id']), row['course_name'], int(row['duration']), exam_students, int(row['priority'])))
      return exams
