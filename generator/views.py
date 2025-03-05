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
import imgkit
from django.http import JsonResponse
from .models import TimetableEntry, Course, Lecturer, Classroom,Timetable
import os
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

                for day in days_shuffled:
                    available_times = list(range(8, 17 - course["duration"]))  # Available time slots (8 AM - 5 PM)
                    random.shuffle(available_times)  # Randomize time slots

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
        timetable[entry.day].update({t: entry.course_name for t in range(start_time, start_time + duration)})
    
    return timetable


def lecturer_timetable_check(request):

    lecturer_id = request.GET.get("lecturer_id")  # Get lecturer ID from dropdown
    selected_year = request.GET.get("year")  # Get selected year
    Alllecturers = Lecturer.objects.all()
    available_years = TimetableEntry.objects.values_list("timetable__intake_year", flat=True).distinct()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    time_slots = TimetableEntry.objects.values("start_time").distinct().order_by("start_time")
    timetable_data = None 
    selected_lecturer = None
        
    if lecturer_id:
        timetable_data = TimetableEntry.objects.filter(
            lecturer_id=lecturer_id
        )
        selected_lecturer = Lecturer.objects.filter(id=lecturer_id).first()

        if selected_year:
            timetable_data = timetable_data.filter(timetable__intake_year=selected_year)
    
    return render(request, "lecturer_timetable_check.html", {
        "alllecturers": Alllecturers,
        "timetable_data": timetable_data,
        "available_years": available_years,
        "selected_year": selected_year,
        "selected_lecturer": selected_lecturer,
        "days": days,
        "time_slots": time_slots
    })
def export_selected_lecturer_timetable_jpeg(request, lecturer_id, selected_year):
    print('nothing now')
#     lecturer = get_object_or_404(Lecturer, id=lecturer_id)

#     # Get the timetable for the selected lecturer and year
#     timetable_data = TimetableEntry.objects.filter(
#             lecturer=lecturer, timetable__intake_year=selected_year
#         )

#     if not timetable_data.exists():
#         return HttpResponse("No timetable found for this selection.", content_type="text/plain")

#     # Generate HTML for the timetable
#     html_code = f"""
#     <html>
#     <head>
#         <style>
#             table {{
#                 width: 100%;
#                 border-collapse: collapse;
#                 text-align: center;
#                 font-family: Arial, sans-serif;
#             }}
#             th, td {{
#                 border: 1px solid black;
#                 padding: 8px;
#             }}
#             th {{
#                 background-color: #f2f2f2;
#             }}
#         </style>
#     </head>
#     <body>
#         <h2>Timetable for {lecturer.name} - {selected_year}</h2>
#         <table>
#             <tr>
#                 <th>Day</th>
#                 <th>Time</th>
#                 <th>Course</th>
#                 <th>Classroom</th>
#             </tr>
#     """

#     for entry in timetable_data:
#         html_code += f"""
#             <tr>
#                 <td>{entry.day}</td>
#                 <td>{entry.start_time} - {entry.end_time}</td>
#                 <td>{entry.course.name}</td>
#                 <td>{entry.classroom.name}</td>
#             </tr>
#         """

#     html_code += """
#         </table>
#     </body>
#     </html>
#     """
#  # Ensure media directory exists
#     # Ensure media directory exists
#     media_path = "media"
#     os.makedirs(media_path, exist_ok=True)

#     # Define file path
#     filename = f"timetable_{lecturer_id}_{selected_year}.jpg"
#     file_path = os.path.join(media_path, filename)

#     # Convert HTML to Image using imgkit
#     imgkit.from_string(html_code, file_path)

#     # Ensure file is created before returning
#     if not os.path.exists(file_path):
#         return HttpResponse("Error: Image generation failed.", content_type="text/plain")

#     # Return image as a download
#     response = FileResponse(open(file_path, "rb"), content_type="image/jpeg")
#     response["Content-Disposition"] = f'attachment; filename="{filename}"'
#     return response
