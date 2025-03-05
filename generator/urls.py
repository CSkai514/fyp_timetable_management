from django.urls import path
from . import views
from .views import format_timetable,upload_csv,generator_function, lecturer_timetable_check,export_selected_lecturer_timetable_jpeg

urlpatterns = [
    path('', views.generator_function, name='generator_function'),
    path("upload_csv/", views.upload_csv, name="upload_csv"),
    path("fetch_timetable/", views.format_timetable, name="fetch_timetable"), 
    path('lecturer_timetable_check/', lecturer_timetable_check, name='lecturer_timetable_check'),
    path("export_selected_lecturer_timetable_jpeg/<int:lecturer_id>/<int:selected_year>/", export_selected_lecturer_timetable_jpeg, name="export_selected_lecturer_timetable_jpeg"),
]
