from django.contrib import admin
from .models import Lecturer, Course, Timetable, Classroom, TimetableEntry



admin.site.register(Lecturer)
admin.site.register(Course)
admin.site.register(Timetable)
admin.site.register(Classroom)
admin.site.register(TimetableEntry)