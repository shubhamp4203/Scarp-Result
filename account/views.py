from re import L
from sys import stdlib_module_names
from unittest import result
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordResetForm, PasswordChangeForm
from django.contrib.auth.models import User, Group
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.http import Http404
from .token import account_activation_token
from django.contrib.auth import get_user_model
import openpyxl
from django.conf import settings
from .models import College, Result, Student, Marks

def check_group(*groups):

    def decorator(function):
        def wrapper(request, *args, **kwargs):
            if request.user.groups.filter(name__in=groups).exists():
                return function(request, *args, **kwargs)
            raise Http404

        return wrapper

    return decorator


'''@csrf_exempt
def registerPage(request):
    if request.user.is_authenticated:
        query_set = Group.objects.filter(user = request.user)
        return redirect(f"{query_set[0]}home")
    else:

        user_form = CreateUserForm()
        profile_form = ProfileForm()

        
        if request.method == "POST":
            user_form = CreateUserForm(request.POST)
            profile_form = ProfileForm(request.POST)

            if user_form.is_valid() and profile_form.is_valid():
                new_user = user_form.save(commit=False)
                new_user.is_active =False
                new_user.save()
                profile = profile_form.save(commit=False)
                if profile.user_id is None:
                    profile.user_id = new_user.id
                profile.save()
                my_group = Group.objects.get(name="Student") 
                my_group.user_set.add(new_user)
                data = user_form.cleaned_data['email']
                associated_users = User.objects.filter(Q(email=data))
                if associated_users.exists():
                    for user in associated_users:
                        subject =  'Activation link has been send to your email id'
                        email_template_name = 'acc_active_email.html'
                        c = {
					"email":user.email,
					'domain':'127.0.0.1:8000',
					'site_name': 'Website',
					"uid": urlsafe_base64_encode(force_bytes(user.pk)),
					"user": user,
					'token': account_activation_token.make_token(user),
					'protocol': 'http',
					}
                    email = render_to_string(email_template_name, c)
                    try:
                        send_mail(subject, email, 'admin@example.com' , [user.email], fail_silently=False)
                        messages.success(request, 'Verification email send. Please verify')
                        return redirect('login')
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
        else:
            user_form = CreateUserForm()
            profile_form = ProfileForm()
    context = {'u_form': user_form, 'p_form': profile_form}
    return render(request, 'register1.html', context)
'''

'''def activate(request, uidb64, token):  
    User = get_user_model()  
    try:  
        uid = force_str(urlsafe_base64_decode(uidb64))  
        user = User.objects.get(pk=uid)  
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):  
        user = None  
    if user is not None and account_activation_token.check_token(user, token):  
        user.is_active = True  
        user.save()  
        messages.success(request, 'Thank you for your email confirmation. Now you can login your account.')
        return redirect('login')  
    else:  
        return HttpResponse('Activation link is invalid!')  '''

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
    if request.method == "GET":
        eroll = request.GET.get('eroll')
        sem = request.GET.get('Semester')
        clgname = request.GET.get('clg')
        if eroll == "" or sem == "" or clgname == "":
            messages.error(request, 'No result found')
            return render(request, 'homepage.html')
        student_info = Student.objects.filter(Q(enrollment_number=eroll) & Q(clg_name=clgname)) 
        if student_info.count()==0:
            messages.error(request, 'No result found')
            return render(request, 'homepage.html')
        result_info = Result.objects.filter(Q(student=student_info[0]) & Q(sem=sem))
        marks_info = Marks.objects.filter(Q(result=result_info[0]))
        for i,j in zip(student_info, result_info):
            seatnumber = j.seat_no
            examname = j.exam_name
            prgname = i.program_name
            stdname = i.name
            cgpa = j.cgpa
            percent = j.percnt
        context = {'cgpa':cgpa, 'percent':percent, 'eroll': eroll, 'clgname': clgname, 'sem':sem, 'seatnumber': seatnumber, 'examname': examname, 'prgname': prgname, 'stdname': stdname, 'marks': marks_info}
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
                if cell.value == None:
                    continue
                row_data.append(str(cell.value))
            excel_data.append(row_data)
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
            for j in range(int((len(row_data)-3)/4)):
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
            result_obj.cgpa = num/denum
            result_obj.percnt = (result_obj.cgpa-0.5)*10
            result_obj.save()
    context = {}
    return render(request, 'admin.html', context)

@login_required(login_url='login')
@check_group("Government")
def governmenthomePage(request):
    context = {}
    return render(request, 'gov_home_page.html', context)


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
        clg_profile = College.objects.create(email=email, clg_name=clgname, approval_pdf=clg_ap_letter)
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
def changeemail(request):
    if request.method == "POST":
        email = request.POST.get('email_id')



