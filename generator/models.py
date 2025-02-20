from django.db import models

class Course(models.Model):
    name = models.CharField(max_length=255)
    duration = models.IntegerField()

class Lecturer(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    unavailable = models.CharField(max_length=255, blank=True, null=True)  # Add this line


class Classroom(models.Model):
    name = models.CharField(max_length=255)

class Timetable(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    day = models.CharField(max_length=10)  # e.g., "Monday"
    start_time = models.IntegerField()  # e.g., 8 for 8 AM

class Student(models.Model):
    student_id = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    courses = models.ManyToManyField(Course)