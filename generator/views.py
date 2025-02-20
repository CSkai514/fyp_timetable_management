from django.shortcuts import render
from django.shortcuts import render, redirect
from .forms import CSVUploadForm
from .generator_engine import *
# Create your views here.
from .models import Timetable
from django.shortcuts import render
from collections import defaultdict
import pandas as pd
from django.views.decorators.csrf import csrf_exempt

def generator_function(request):

    return render(request, 'generator.html')


import csv
import random
from io import TextIOWrapper
from django.http import JsonResponse

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
HOURS = list(range(8, 17))  # 8 AM to 5 PM

@csrf_exempt
def generate_timetable(request):
    if request.method == "POST" and request.FILES.get("timetable"):
        uploaded_file = request.FILES["timetable"]
        csv_file = TextIOWrapper(uploaded_file.file, encoding="utf-8")
        reader = csv.reader(csv_file)

        students, courses, lecturers, classrooms = [], [], [], []
        section = None

        # Read CSV Data
        for row in reader:
            if not row or row[0].strip() == "":
                continue  # Skip empty lines

            if row[0] == "Students":
                section = "students"
                continue
            elif row[0] == "Courses":
                section = "courses"
                continue
            elif row[0] == "Lecturers":
                section = "lecturers"
                continue
            elif row[0] == "Classrooms":
                section = "classrooms"
                continue

            try:
                if section == "students":
                    students.append({"id": row[0], "name": row[1], "student_id": row[2]})
                elif section == "courses":
                    if row[0].lower() != "name" and row[1].lower() != "duration":  # Avoid headers
                        courses.append({"name": row[0], "duration": int(row[1])})
                elif section == "lecturers":
                    if row[0].lower() != "name" and row[1].lower() != "courses":  # Avoid headers
                        lecturers.append({"name": row[0], "courses": row[1].split(",")})
                elif section == "classrooms":
                    if row[0].lower() != "name" and row[1].lower() != "capacity":  # Avoid headers
                        classrooms.append({"name": row[0], "capacity": int(row[1])})
            except (ValueError, IndexError) as e:
                print(f"⚠ Error processing row: {row} - {e}")

        # Create Empty Timetable Structure
        timetable = {hour: {day: None for day in DAYS} for hour in HOURS}

        # Assign Courses
        for course in courses:
            assigned = False
            available_lecturers = [l for l in lecturers if course["name"] in l["courses"]]

            if not available_lecturers:
                print(f"⚠ Warning: No lecturer available for {course['name']}")
                continue  # Skip scheduling this course

            for _ in range(100):  # Retry limit
                day = random.choice(DAYS)
                start_hour = random.choice(HOURS[:-course["duration"]])

                # Check if slot is available
                if all(timetable[h][day] is None for h in range(start_hour, start_hour + course["duration"])):
                    lecturer = random.choice(available_lecturers)  # Pick from available lecturers
                    classroom = random.choice(classrooms)

                    for h in range(start_hour, start_hour + course["duration"]):
                        timetable[h][day] = {
                            "course": course["name"],
                            "lecturer": lecturer["name"],
                            "classroom": classroom["name"],
                        }

                    assigned = True
                    break

            if not assigned:
                print(f"⚠ Could not schedule {course['name']}")

        return JsonResponse({"timetable": timetable})
    
    return JsonResponse({"error": "Invalid request"}, status=400)