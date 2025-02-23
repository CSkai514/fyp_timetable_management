from django.db import models


class Course(models.Model):
    name = models.CharField(max_length=255, unique=True)
    duration = models.IntegerField(help_text="Duration in hours")

    def __str__(self):
        return f"{self.name} ({self.duration} hrs)"
    



class Classroom(models.Model):
    name = models.CharField(max_length=50, unique=True)
    capacity = models.IntegerField(default=15)  # Set default value here

    def __str__(self):
        return self.name

class Timetable(models.Model):
    intake_year = models.IntegerField(null=True,default="2025")
    intake_month = models.CharField(max_length=20, default="January")
    program = models.CharField(max_length=255, null=True)
    
    class Meta:
        unique_together = ('intake_year', 'intake_month', 'program')

    def __str__(self):
        return f"{self.program} - {self.intake_month} {self.intake_year}"
    
class Lecturer(models.Model):
    name = models.CharField(max_length=255, unique=True)
    courses = models.ManyToManyField(Course, related_name="lecturers")  # Many-to-Many Relationship

    def __str__(self):
        return self.name
    
class TimetableEntry(models.Model):
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name="entries")
    lecturer = models.ForeignKey(Lecturer, on_delete=models.SET_NULL, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    classroom = models.ForeignKey(Classroom, on_delete=models.SET_NULL, null=True)
    day = models.CharField(max_length=20, choices=[("Monday", "Monday"), ("Tuesday", "Tuesday"), ("Wednesday", "Wednesday"), ("Thursday", "Thursday"), ("Friday", "Friday")])
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ('day', 'start_time', 'classroom')

    def __str__(self):
        return f"{self.course.name} - {self.day} ({self.start_time} - {self.end_time})"
