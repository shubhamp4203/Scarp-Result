from re import L
from sys import stdlib_module_names
from django.core.files.storage import default_storage
from unittest import result
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, BadHeaderError
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordResetForm, PasswordChangeForm
from django.contrib.auth.models import User, Group
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.http import Http404, FileResponse
from .token import account_activation_token
from django.contrib.auth import get_user_model
import openpyxl
import uuid
import string
import random
from django.conf import settings
from .models import College, Result, Student, Marks
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404


def check_group(*groups):

    def decorator(function):
        def wrapper(request, *args, **kwargs):
            if request.user.groups.filter(name__in=groups).exists():
                return function(request, *args, **kwargs)
            raise Http404

        return wrapper

    return decorator

def generate_username_and_password():
    characters = string.ascii_letters + string.digits + string.punctuation
    username_length = 5
    username = ''.join(random.choice(characters) for i in range(username_length))
    return username

def generate_django_password(length=12):
    chars = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(chars) for i in range(length))
    while not any(c.islower() for c in password) or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
        password = ''.join(random.choice(chars) for i in range(length))
    return password


@csrf_exempt
def loginPage(request):
    if request.user.is_authenticated:
        query_set = Group.objects.filter(user = request.user)
        return redirect(f"{query_set[0]}home")
    else:
        if request.method == "POST":
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                query_set = Group.objects.filter(user = user)
                login(request, user)
                return redirect(f"{query_set[0].name}home")
            else:
                messages.info(request, 'Username or password is incorrect')
        context={}
        return render(request, 'login.html', context)

def homepage(request):
    if request.method == "POST":
        eroll = request.POST.get('eroll')
        sem = request.POST.get('Semester')
        clgname = request.POST.get('clg')
        if eroll == "" or sem == "" or clgname == "":
            messages.error(request, 'No result found')
            return redirect('home')
        student_info = Student.objects.filter(Q(enrollment_number=eroll) & Q(clg_name=clgname)) 
        if student_info.count()==0:
            messages.error(request, 'No result found')
            return redirect('home')
        result_info = Result.objects.filter(Q(student=student_info[0]) & Q(sem=sem))
        if result_info.count()==0:
            messages.error(request, 'No result found')
            return redirect('home')
        marks_info = Marks.objects.filter(Q(result=result_info[0]))
        for i,j in zip(student_info, result_info):
            seatnumber = j.seat_no
            examname = j.exam_name
            prgname = i.program_name
            stdname = i.name
            sgpa = j.sgpa
            percent = j.percnt
        context = {'sgpa':sgpa, 'percent':percent, 'eroll': eroll, 'clgname': clgname, 'sem':sem, 'seatnumber': seatnumber, 'examname': examname, 'prgname': prgname, 'stdname': stdname, 'marks': marks_info}
        return render(request, 'test_result.html', context)
    context = {}
    return render(request, 'homepage.html', context)

@csrf_exempt
@login_required(login_url='login')
@check_group("Institute")
def institutehomePage(request):
    if request.method == "POST":
        clgname = request.POST.get('clg')
        prgname = request.POST.get('program')
        examname=request.POST.get('exam')
        semester = request.POST.get('Semester')
        excel_file = request.FILES["excel_file"]
        wb = openpyxl.load_workbook(excel_file)
        worksheet = wb["Sheet1"]
        excel_data = []
        for row in worksheet.iter_rows(min_row=2):
            row_data=[]
            for cell in row:
                if cell.value is None:
                    continue
                row_data.append(str(cell.value))
            excel_data.append(row_data)
        for i in excel_data:
            if i == []:
                excel_data.remove(i)
        if len(excel_data[-1]) == 0:
            excel_data.pop()
        for i in excel_data:
            try:
                student_obj = Student.objects.get(name=i[0])
            except:
                student_obj = None
            if student_obj is None:
                student_obj = Student.objects.create(name=i[0], enrollment_number=i[1], clg_name=clgname, program_name=prgname)
            student_obj.save()
            result_obj = Result.objects.create(student=student_obj, sem=semester, exam_name=examname, seat_no = i[2])
            result_obj.save()
            ccode_index = 3
            ccredit_index = 4
            cname_index = 5
            cmarks_index = 6
            for j in range(int((len(excel_data[0])-3)/4)):
                marks_obj = Marks.objects.create(result=result_obj, course_code = i[ccode_index], course_credit=i[ccredit_index], course_name=i[cname_index], grade=i[cmarks_index])
                marks_obj.save()
                ccode_index += 4
                ccredit_index += 4
                cname_index += 4
                cmarks_index += 4
            grade_cal = Marks.objects.filter(result=result_obj)
            num = 0.0
            denum = 0.0 
            for i in grade_cal:
                num += i.grade*i.course_credit
                denum += i.course_credit
            result_obj.sgpa = round(num/denum)
            result_obj.percnt = (result_obj.sgpa-0.5)*10
            result_obj.save()
        messages.success(request, "Result uploaded successfully")
    context = {}
    return render(request, 'admin.html', context)

@login_required(login_url='login')
@check_group("Government")
def governmenthomePage(request):
    allstu = Student.objects.all().prefetch_related('result_set').order_by('-result__created_at')
    paginator = Paginator(allstu, 10)
    page = request.GET.get('page')
    stupage = paginator.get_page(page)
    if request.method == 'GET':
        sem = request.GET.get('Semester')
        clg_name = request.GET.get('clg')
        if sem:
            allstu = allstu.filter(result__sem=sem)
        if clg_name:
            allstu = allstu.filter(clg_name=clg_name)
    paginator = Paginator(allstu, 10)
    page = request.GET.get('page')
    stupage = paginator.get_page(page)   
            
            
    context = {'students': allstu, 'studentpage': stupage}
    return render(request, 'GovBox.html', context)


def logoutUser(request):
    logout(request)
    return redirect('login')

@csrf_exempt
def password_reset_request(request):
	if request.method == "POST":
		password_reset_form = PasswordResetForm(request.POST)
		if password_reset_form.is_valid():
			data = password_reset_form.cleaned_data['email']
			associated_users = User.objects.filter(Q(email=data))
			if associated_users.exists():
				for user in associated_users:
					subject = "Password Reset Requested"
					email_template_name = "password_reset_email.txt"
					c = {
					"email":user.email,
					'domain':'127.0.0.1:8000',
					'site_name': 'Website',
					"uid": urlsafe_base64_encode(force_bytes(user.pk)),
					"user": user,
					'token': default_token_generator.make_token(user),
					'protocol': 'http',
					}
					email = render_to_string(email_template_name, c)
					try:
						send_mail(subject, email, settings.EMAIL_HOST_USER , [user.email], fail_silently=False)
					except BadHeaderError:
						return HttpResponse('Invalid header found.')
					return redirect ("password_reset_done")
	password_reset_form = PasswordResetForm()
	return render(request=request, template_name="password_reset.html", context={"password_reset_form":password_reset_form})

def scholarshippage(request):
    context = {}
    return render(request, 'Scholarshipdetails.html',  context)

def collegeregister(request):
    if request.method == "POST":
        email = request.POST.get('email_id')
        clgname = request.POST.get('college_name')
        clg_ap_letter = request.FILES['government_approval_letter']
        file_name = f"{clgname}.pdf"
        file_path = default_storage.save(file_name, clg_ap_letter)
        clg_profile = College.objects.create(email=email, clg_name=clgname, approval_pdf=file_path)
        clg_profile.save()
        user_admin = User.objects.get(username="ClawX69")
        admin_email = user_admin.email
        subject = "College Registration Requested"
        email_template_name = "college_registration_email.txt"
        c = {
				"email":admin_email,
				'domain':'127.0.0.1:8000',
				'site_name': 'Website',
				'protocol': 'http',
			}
        emailrender = render_to_string(email_template_name, c)
        try:
            send_mail(subject, emailrender, settings.EMAIL_HOST_USER , [admin_email], fail_silently=False)
        except BadHeaderError:
            return HttpResponse('Invalid header found.')
        return render(request, 'register_college.html')
    context = {}
    return render(request, 'register_college.html', context)

def contactdetail(request):
    context = {}
    return render(request, 'contact.html', context)

@login_required(login_url='login')
@check_group("Admin")
def adminpage(request):
    pendingclg = College.objects.filter(status="Pending").order_by("-created_at")
    paginator = Paginator(pendingclg, 10)
    page = request.GET.get('page')
    pendingclg = paginator.get_page(page)
    context = {'pclg': pendingclg}
    return render(request, 'superadmin.html', context=context)

def accept(request, clg_name):
    clg = get_object_or_404(College, clg_name=clg_name)
    clg.status = "Approved"
    clg.save()
    uname = generate_username_and_password()
    passw = f"scrap@university"
    newuser = User.objects.create_user(username=uname, password=passw, email=clg.email)
    my_group = Group.objects.get(name='Institute') 
    my_group.user_set.add(newuser)
    newuser.save()
    subject = "College approved!"
    c = {
            "email":clg.email,
            'domain':'127.0.0.1:8000',
            'site_name': 'Website',
            'protocol': 'http',
            'uname': uname,
            'passw': passw
		}
    emailrender = render_to_string('clg_approved.txt', c)
    try:
        send_mail(subject, emailrender, settings.EMAIL_HOST_USER , [clg.email], fail_silently=False)
    except BadHeaderError:
        return HttpResponse('Invalid header found.')
    pendingclg = College.objects.filter(status="Pending").order_by("-created_at")
    paginator = Paginator(pendingclg, 10)
    page = request.GET.get('page')
    pendingclg = paginator.get_page(page)
    context = {'pclg': pendingclg}
    return render(request, 'superadmin.html', context=context)

def reject(request, clg_name):
    clg = get_object_or_404(College, clg_name=clg_name)
    subject = "College Rejected!"
    c = {
            "email":clg.email,
            'domain':'127.0.0.1:8000',
            'site_name': 'Website',
            'protocol': 'http',
		}
    emailrender = render_to_string('clg_rejected.txt', c)
    try:
        send_mail(subject, emailrender, settings.EMAIL_HOST_USER , [clg.email], fail_silently=False)
    except BadHeaderError:
        return HttpResponse('Invalid header found.')
    clg.delete()
    pendingclg = College.objects.filter(status="Pending").order_by("-created_at")
    paginator = Paginator(pendingclg, 10)
    page = request.GET.get('page')
    pendingclg = paginator.get_page(page)
    context = {'pclg': pendingclg}
    return render(request, 'superadmin.html', context=context)

        

def adminlogin(request):
    if request.user.is_authenticated:
        query_set = Group.objects.filter(user = request.user)
        return redirect(f"{query_set[0]}home")
    else:
        if request.method == "POST":
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                query_set = Group.objects.filter(user = user)
                login(request, user)
                return redirect(f"{query_set[0].name}home")
            else:
                messages.info(request, 'Username or password is incorrect')
        context={}
        return render(request, 'adminlogin.html', context)

def student_detail(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    result = Result.objects.get(student=student)
    clgname = student.clg_name
    stdname = student.name
    prgname = student.program_name
    eroll = student.enrollment_number
    sem = result.sem
    seat_no = result.seat_no
    sgpa = result.sgpa
    percnt = result.percnt
    exam_name = result.exam_name
    marks_info = Marks.objects.filter(Q(result=result))

    context = {'sgpa':sgpa, 'percent':percnt, 'eroll': eroll, 'clgname': clgname, 'sem':sem, 'seatnumber': seat_no, 'examname': exam_name, 'prgname': prgname, 'stdname': stdname, 'marks': marks_info}


    return render(request, 'student_detail.html', context)

@login_required(login_url='login')
@check_group("Admin")
def approvedreq(request):
    approvedclg = College.objects.filter(status="Approved").order_by("-created_at")
    paginator = Paginator(approvedclg, 10)
    page = request.GET.get('page')
    approvedclg = paginator.get_page(page)
    context = {'pclg': approvedclg}
    return render(request, 'approvedclg.html', context=context)

def clg_letter(request, clg_id):
    clg = get_object_or_404(College, pk=clg_id)
    file_path = 'media/' + f"{clg.clg_name}.pdf"
    return FileResponse(open(file_path, 'rb'), content_type='application/pdf')








