from django.shortcuts import render
from django.shortcuts import render, redirect
from .forms import CSVUploadForm
from .generator_engine import *
# Create your views here.
from .models import Timetable

def generator_function(request):

    return render(request, 'generator.html')

