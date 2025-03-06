import os
from django.shortcuts import render, redirect, get_object_or_404
# from .forms import CSVUploadForm, IntakeSelectionForm
from collections import defaultdict
import pandas as pd
from django.views.decorators.csrf import csrf_exempt
import csv
import random
from collections import defaultdict
from io import TextIOWrapper
from django.http import FileResponse, HttpResponse

from django.http import JsonResponse
from .models import TimetableEntry, Course, Lecturer, Classroom,Timetable
from datetime import datetime, timedelta
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

            uploaded_course_names = [row["Name"].strip() for row in reader]
            existing_courses = Course.objects.filter(name__in=uploaded_course_names)
            course_dict = {course.name: course for course in existing_courses}

            courses = []
            for row in decoded_file[1:]:
                course_name = row.split(",")[0].strip()

                if course_name not in course_dict:
                    return JsonResponse({"error": f"Course '{course_name}' does not exist in the database."}, status=400)

                course_obj = course_dict[course_name]
                course_duration = course_obj.duration

                courses.append({"name": course_name, "duration": course_duration, "course_obj": course_obj})

            classrooms = list(Classroom.objects.all())
            if not classrooms:
                return JsonResponse({"error": "Something went wrong, Reason: No classrooms available. Please add classrooms first."}, status=400)
            
            for course in courses:
                qualified_lecturers = Lecturer.objects.filter(courses=course["course_obj"])
                if not qualified_lecturers.exists():
                    return JsonResponse({"error": f"No qualified lecturers for course '{course['name']}'."}, status=400)
            

            timetable_data = {day: {} for day in DAYS}

            for course in courses:
                assigned = False 

                # Get lecturers who can teach this course
                qualified_lecturers = list(Lecturer.objects.filter(courses=course["course_obj"]))
                if not qualified_lecturers:
                    return JsonResponse({"error": f"No qualified lecturers for course '{course['name']}'."}, status=400)

                days_shuffled = list(timetable_data.keys())
                random.shuffle(days_shuffled)

                for day in days_shuffled:
                    available_times = list(range(8, 17 - course["duration"]))
                    random.shuffle(available_times)
                    for start_time in available_times:
                        if any(t in timetable_data[day] for t in range(start_time, start_time + course["duration"])):
                            continue 

                        available_lecturers = [
                            lecturer for lecturer in qualified_lecturers
                            if all(t not in timetable_data[day].get(lecturer.name, []) for t in range(start_time, start_time + course["duration"]))
                        ]
                        if not available_lecturers:
                            continue 

                        available_classrooms = [
                                classroom for classroom in classrooms
                                if not TimetableEntry.objects.filter(
                                    timetable__intake_year=timetable.intake_year,
                                    timetable__intake_month=timetable.intake_month,
                                    #timetable__semester=timetable.semester,
                                    classroom=classroom,
                                    day=day,
                                    start_time__lt=f"{start_time + course['duration']}:00",
                                    end_time__gt=f"{start_time}:00"
                                ).exists()
                            ]
                        if not available_classrooms:
                            continue

                        lecturer = random.choice(available_lecturers)
                        classroom = random.choice(available_classrooms)

                        TimetableEntry.objects.create(
                            timetable=timetable,
                            lecturer=lecturer,
                            course=course["course_obj"],
                            classroom=classroom,
                            day=day,
                            start_time=f"{start_time}:00",
                            end_time=f"{start_time + course['duration']}:00"
                        )

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
                        break

                    if assigned:
                        break

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
        timetable[entry.day].update({t: entry.course.name for t in range(start_time, start_time + duration)})
    
    return timetable


def lecturer_timetable_check(request):
    lecturer_id = request.GET.get("lecturer_id")
    selected_year = request.GET.get("year")

    Alllecturers = Lecturer.objects.all()
    available_years = TimetableEntry.objects.values_list("timetable__intake_year", flat=True).distinct()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    time_slots = [
        "08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM",
        "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM"
    ]

    timetable_data = {day: [] for day in days}  # Grouped by day
    selected_lecturer = None
    if lecturer_id:
        query = TimetableEntry.objects.filter(lecturer_id=lecturer_id)
        selected_lecturer = Lecturer.objects.filter(id=lecturer_id).first()
        if selected_year:
            query = query.filter(timetable__intake_year=selected_year)

        for entry in query:
            start_hour = int(entry.start_time.strftime("%H"))
            end_hour = int(entry.end_time.strftime("%H"))
            duration_hours = end_hour - start_hour  # Calculate duration
            start_time_str = entry.start_time.strftime("%I:%M %p")
            end_time_str = entry.end_time.strftime("%I:%M %p")

            timetable_data[entry.day].append({
                "start_time": start_time_str,
                "end_time": end_time_str,
                "duration": duration_hours,
                "course": entry.course.name,
                "lecturer": entry.lecturer.name,
                "classroom": entry.classroom.name
            })

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
    # Convert timetable_data dictionary into an array of objects with a day as the key
        response_data = {
            "timetable_data": [
                {"day": day, "entries": entries} 
                for day, entries in timetable_data.items()
            ]
        }
        return JsonResponse(response_data)

    return render(request, "lecturer_timetable_check.html", {
        "alllecturers": Alllecturers,
        "timetable_data": timetable_data,
        "available_years": available_years,
        "selected_year": selected_year,
        "days": days,
        "time_slots": time_slots,
        "selected_lecturer": selected_lecturer,
    })

