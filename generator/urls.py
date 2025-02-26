from django.urls import path
from . import views
from .views import format_timetable,upload_csv,generator_function

urlpatterns = [
    path('', views.generator_function, name='generator_function'),
    path("upload_csv/", views.upload_csv, name="upload_csv"),  # Upload CSV file
    path("fetch_timetable/", views.format_timetable, name="fetch_timetable"),  # Fetch timetable for selected intake
]
