
import csv
from io import TextIOWrapper
from django.core.exceptions import ValidationError
from .models import Course, Lecturer, Classroom, Student

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
TIME_SLOTS = list(range(8, 17))  # 8 AM to 4 PM

# CSV Processor



