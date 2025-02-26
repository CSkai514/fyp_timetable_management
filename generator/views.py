from django.shortcuts import render, redirect
# from .forms import CSVUploadForm, IntakeSelectionForm
from collections import defaultdict
import pandas as pd
from django.views.decorators.csrf import csrf_exempt
import csv
import random
from collections import defaultdict
from io import TextIOWrapper
from django.http import JsonResponse
from .models import TimetableEntry, Course, Lecturer, Classroom,Timetable
# Create your views here.

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
HOURS = list(range(8, 17))  # 8 AM to 5 PM


def generator_function(request):

    return render(request, 'generator.html')


@csrf_exempt
def upload_csv(request):
    if request.method == "POST" and request.FILES.get("timetable"):
        intake_year = request.POST.get("intake_year")
        intake_month = request.POST.get("intake_month")
        program = request.POST.get("program")

        # Fetch or create the Timetable instance
        timetable, created = Timetable.objects.get_or_create(
            intake_year=intake_year,
            intake_month=intake_month,
            program=program
        )

        #  If timetable already exists, return it instead of generating a new one
        existing_timetable_data = TimetableEntry.objects.filter(timetable=timetable)
        if existing_timetable_data.exists():
            timetable_data = {day: {} for day in DAYS}
            for database_existing_data in existing_timetable_data:
                start_hour = int(database_existing_data.start_time.strftime("%H"))
                end_hour = int(database_existing_data.end_time.strftime("%H"))

                for t in range(start_hour, end_hour):
                    if t not in timetable_data[database_existing_data.day]:
                        timetable_data[database_existing_data.day][t] = []

                    timetable_data[database_existing_data.day][t].append({
                        "course": database_existing_data.course.name,
                        "lecturer": database_existing_data.lecturer.name,
                        "classroom": database_existing_data.classroom.name
                    })

            return JsonResponse({"timetable": timetable_data, "message": "Existing timetable detected, Existing Timetable loaded!"})
        else:
            file = request.FILES["timetable"]
            decoded_file = file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded_file)

            # Fetch only course names from the uploaded CSV
            uploaded_course_names = [row["Name"].strip() for row in reader]
            existing_courses = Course.objects.filter(name__in=uploaded_course_names)
            course_dict = {course.name: course for course in existing_courses}

            courses = []
            for row in decoded_file[1:]:
                course_name = row.split(",")[0].strip()

                if course_name not in course_dict:
                    return JsonResponse({"error": f"Course '{course_name}' does not exist in the database."}, status=400)

                # Fetch duration from the database
                course_obj = course_dict[course_name]
                course_duration = course_obj.duration  # Use duration from DB

                courses.append({"name": course_name, "duration": course_duration, "course_obj": course_obj})

            # Get available classrooms and lecturers
            classrooms = list(Classroom.objects.all())
            if not classrooms:
                return JsonResponse({"error": "Something went wrong, Reason: No classrooms available. Please add classrooms first."}, status=400)
            
            for course in courses:
                qualified_lecturers = Lecturer.objects.filter(courses=course["course_obj"])
                if not qualified_lecturers.exists():
                    return JsonResponse({"error": f"No qualified lecturers for course '{course['name']}'."}, status=400)
            

            timetable_data = {day: {} for day in DAYS}

            for course in courses:
                assigned = False  # Track if the course is successfully scheduled

                # Get lecturers who can teach this course
                qualified_lecturers = list(Lecturer.objects.filter(courses=course["course_obj"]))
                if not qualified_lecturers:
                    return JsonResponse({"error": f"No qualified lecturers for course '{course['name']}'."}, status=400)

                # Shuffle days to randomize selection
                days_shuffled = list(timetable_data.keys())
                random.shuffle(days_shuffled)

                # Try assigning a timeslot within Monday–Friday
                for day in days_shuffled:
                    available_times = list(range(8, 17 - course["duration"]))  # Available time slots (8 AM - 5 PM)
                    random.shuffle(available_times)  # Randomize time slots

                    for start_time in available_times:
                        # Check if this time slot is free
                        if any(t in timetable_data[day] for t in range(start_time, start_time + course["duration"])):
                            continue  # Skip if time slot is occupied

                        # Get available lecturers
                        available_lecturers = [
                            lecturer for lecturer in qualified_lecturers
                            if all(t not in timetable_data[day].get(lecturer.name, []) for t in range(start_time, start_time + course["duration"]))
                        ]
                        if not available_lecturers:
                            continue  # Skip if no lecturer is available

                        # Get available classrooms
                        available_classrooms = [
                            classroom for classroom in classrooms
                            if all(t not in timetable_data[day].get(classroom.id, []) for t in range(start_time, start_time + course["duration"]))
                        ]
                        if not available_classrooms:
                            continue  # Skip if no classroom is available

                        # Randomly assign a lecturer and a classroom
                        lecturer = random.choice(available_lecturers)
                        classroom = random.choice(available_classrooms)

                        # Save the entry to the database
                        TimetableEntry.objects.create(
                            timetable=timetable,
                            lecturer=lecturer,
                            course=course["course_obj"],
                            classroom=classroom,
                            day=day,
                            start_time=f"{start_time}:00",
                            end_time=f"{start_time + course['duration']}:00"
                        )

                        # Update timetable_data to track booked slots
                        for t in range(start_time, start_time + course["duration"]):
                            if t not in timetable_data[day]:
                                timetable_data[day][t] = []
                            timetable_data[day][t].append({
                                "course": course["name"],
                                "lecturer": lecturer.name,
                                "classroom": classroom.name
                            })
                            timetable_data[day].setdefault(lecturer.name, []).append(t)  # Mark lecturer's time as booked
                            timetable_data[day].setdefault(classroom.id, []).append(t)  # Mark classroom's time as booked

                        assigned = True  # Mark as assigned
                        break  # Exit time loop

                    if assigned:
                        break  # Exit day loop

                if not assigned:
                    return JsonResponse({"error": f"Could not assign course '{course['name']}' due to scheduling conflicts."}, status=400)

            return JsonResponse({"timetable": timetable_data, "message": "New timetable generated successfully!",}, status=200, json_dumps_params={'indent': 2})


    return JsonResponse({"error": "Invalid request"}, status=400)



def format_timetable(entries):
    timetable = {day: {} for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}
    
    for entry in entries:
        time_range = f"{entry.start_time.strftime('%H:%M')} - {entry.end_time.strftime('%H:%M')}"
        start_time = int(time_range[0].replace(":00AM", "").replace(":00PM", ""))
        duration = int(time_range[1].replace(":00AM", "").replace(":00PM", "")) - start_time
        timetable[entry.day].update({t: entry.course_name for t in range(start_time, start_time + duration)})
    
    return timetable