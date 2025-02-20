from django.urls import path
from . import views
from .views import generate_timetable

urlpatterns = [
    path('', views.generator_function),
    path("generate_timetable/", views.generate_timetable, name="generate_timetable"),
]
