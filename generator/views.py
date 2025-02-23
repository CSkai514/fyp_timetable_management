from django.shortcuts import render, redirect
# from .forms import CSVUploadForm, IntakeSelectionForm
from collections import defaultdict
import pandas as pd
from django.views.decorators.csrf import csrf_exempt
import csv
import random
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
        existing_entries = TimetableEntry.objects.filter(timetable=timetable)
        if existing_entries.exists():
            timetable_data = {day: {} for day in DAYS}
            for entry in existing_entries:
                start_hour = int(entry.start_time.strftime("%H"))
                end_hour = int(entry.end_time.strftime("%H"))

                for t in range(start_hour, end_hour):
                    if t not in timetable_data[entry.day]:
                        timetable_data[entry.day][t] = []

                    timetable_data[entry.day][t].append({
                        "course": entry.course.name,
                        "lecturer": entry.lecturer.name,
                        "classroom": entry.classroom.name
                    })

            return JsonResponse({"timetable": timetable_data, "message": "Existing timetable loaded!"})
        else:
            #  Read CSV
            file = request.FILES["timetable"]
            decoded_file = file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(decoded_file)

            #  Fetch only courses from the uploaded CSV
            uploaded_course_names = [row["Name"].strip() for row in reader]
            existing_courses = Course.objects.filter(name__in=uploaded_course_names)
            course_dict = {course.name: course for course in existing_courses}

            courses = []
            for row in decoded_file[1:]:
                course_name = row.split(",")[0].strip()
                duration_str = row.split(",")[1].strip()

                if not duration_str.isdigit():
                    return JsonResponse({"error": f"Invalid duration: {duration_str}. Must be a number."}, status=400)

                if course_name not in course_dict:
                    return JsonResponse({"error": f"Course '{course_name}' does not exist in the database."}, status=400)

                courses.append({"name": course_name, "duration": int(duration_str), "course_obj": course_dict[course_name]})

            #  Get available classrooms and lecturers
            classrooms = list(Classroom.objects.all())
            if not classrooms:
                return JsonResponse({"error": "No classrooms available. Please add classrooms first."}, status=400)

            timetable_data = {day: {} for day in DAYS}

            for course in courses:
                assigned = False
                while not assigned:
                    day = random.choice(DAYS)
                    course_duration = course["duration"]
                    start_time = random.randint(8, 17 - course_duration)

                    #  Only pick lecturers who can teach this course
                    qualified_lecturers = Lecturer.objects.filter(courses=course["course_obj"])
                    if not qualified_lecturers.exists():
                        return JsonResponse({"error": f"No qualified lecturers for course '{course['name']}'."}, status=400)

                    if all(t not in timetable_data[day] for t in range(start_time, start_time + course_duration)):
                        lecturer = random.choice(list(qualified_lecturers))
                        classroom = random.choice(classrooms)

                        # Save to the database
                        TimetableEntry.objects.create(
                            timetable=timetable,
                            lecturer=lecturer,
                            course=course["course_obj"],
                            classroom=classroom,
                            day=day,
                            start_time=f"{start_time}:00",
                            end_time=f"{start_time + course_duration}:00"
                        )

                        #  Store data correctly in timetable_data
                        for t in range(start_time, start_time + course_duration):
                            if t not in timetable_data[day]:
                                timetable_data[day][t] = []

                            timetable_data[day][t].append({
                                "course": course["name"],
                                "lecturer": lecturer.name,
                                "classroom": classroom.name
                            })

                        assigned = True

            return JsonResponse({"timetable": timetable_data, "message": "New timetable generated successfully!"})

    return JsonResponse({"error": "Invalid request"}, status=400)



def format_timetable(entries):
    timetable = {day: {} for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}
    
    for entry in entries:
        time_range = f"{entry.start_time.strftime('%H:%M')} - {entry.end_time.strftime('%H:%M')}"
        start_time = int(time_range[0].replace(":00AM", "").replace(":00PM", ""))
        duration = int(time_range[1].replace(":00AM", "").replace(":00PM", "")) - start_time
        timetable[entry.day].update({t: entry.course_name for t in range(start_time, start_time + duration)})
    
    return timetable