from enum import unique
from tkinter import CASCADE
from unittest.util import _MAX_LENGTH
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist


# Create your models here.


class College(models.Model):
    email = models.EmailField(null=True)
    clg_name = models.CharField(max_length=200, null=True, unique=True)
    approval_pdf = models.FileField()

class Student(models.Model):
    name = models.CharField(max_length=100, blank=False)
    enrollment_number = models.IntegerField(unique=True, null=True, blank=False)
    clg_name = models.CharField(max_length=200, blank=False)
    program_name = models.CharField(max_length=30, blank=False)

class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    sem = models.IntegerField()
    exam_name = models.CharField(max_length=30)
    percnt = models.FloatField(null=True)
    sgpa = models.FloatField(null=True)
    seat_no = models.CharField(unique=True, max_length=30, null=True)

class Marks(models.Model):
    result = models.ForeignKey(Result, on_delete=models.CASCADE)
    course_name = models.CharField(max_length=100, null=True)
    course_code = models.IntegerField(null=True)
    course_credit = models.IntegerField(null=True)    
    grade = models.FloatField(null=True)



