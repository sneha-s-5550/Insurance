from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate, login as auth_login 
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import check_password
from .models import Agent,Campaign,Client
import random, string
from django.contrib.auth.models import auth
import re
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


# Create your views here.
def home(request):
    return render(request,'home.html')

def loginpage(request):
    return render(request,'loginpage.html')

def logout(request):
    auth.logout(request)
    return redirect('home')

def log(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip()
        password = request.POST.get('pass').strip()  # match your form

        # -------- 1️⃣ Try Django admin/staff login --------
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)  # Django session
            if user.is_staff or user.is_superuser:
                return redirect('admindash')  # admin dashboard
            else:
                return redirect('agent_dash')  # rare case if non-staff Django user

        # -------- 2️⃣ If not staff, try Agent model login --------
        agent = Agent.objects.filter(username=username, is_active=True).first()
        if agent and check_password(password, agent.password):
            # session for agent
            request.session['agent_id'] = agent.id
            request.session['agent_name'] = agent.first_name
            return redirect('agent_dash')

        # -------- 3️⃣ Invalid credentials --------
        messages.error(request, "Invalid Username or Password")
        return redirect('loginpage')

    return render(request, 'loginpage.html')

def admindash(request):
    return render(request,'admindash.html')

def agent_dash(request):
    if not request.session.get('agent_id'):
        return redirect('loginpage')

    return render(request, 'agent_dash.html')



def add_agent(request):
    if request.method == "POST":

        username = request.POST.get('username')
        email = request.POST.get('email')

        # Duplicate check
        if Agent.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('add_agent')

        if Agent.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('add_agent')

        # 6 digit password
        raw_password = ''.join(random.choices(string.digits, k=6))

        agent = Agent.objects.create(
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            username=username,
            email=email,
            password=make_password(raw_password),
            profile_image=request.FILES.get('profile_image'),
            age=request.POST.get('age') or None,
            qualification=request.POST.get('qualification'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            district=request.POST.get('district'),
        )

        # Email
        send_mail(
            "Agent Login Credentials",
            f"Username: {username}\nPassword: {raw_password}",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False
        )

        messages.success(request, "Agent added & email sent successfully")
        return redirect('add_agent')

    return render(request, 'add_agent.html')

def check_agent_exists(request):
    field = request.GET.get("field")
    value = request.GET.get("value")
    agent_id = request.GET.get("agent_id")  # optional

    # safety check
    if not field or not value:
        return JsonResponse({"exists": False})

    qs = Agent.objects.all()

    # EDIT page case → ignore current agent
    if agent_id:
        qs = qs.exclude(id=agent_id)

    if field not in ["email", "username", "phone"]:
        return JsonResponse({"exists": False})

    exists = qs.filter(**{field: value}).exists()

    return JsonResponse({"exists": exists})

def agent_list(request):
    agents = Agent.objects.all().order_by('-joined_on')  # latest first
    return render(request, 'view_agent.html', {'agents': agents})

def edit_agent(request, id):
    agent = get_object_or_404(Agent, id=id)

    if request.method == "POST":
        username = request.POST.get("username")

        # ✅ Exclude current agent
        if Agent.objects.filter(username=username).exclude(id=agent.id).exists():
            messages.error(request, "Username already exists")
            return redirect("edit_agent", id=agent.id)

    if request.method == "POST":
        agent.first_name = request.POST.get('first_name')
        agent.last_name = request.POST.get('last_name')
        agent.email = request.POST.get('email')
        agent.phone = request.POST.get('phone')
        agent.age = request.POST.get('age') or None
        agent.qualification = request.POST.get('qualification')
        agent.address = request.POST.get('address')
        agent.city = request.POST.get('city')
        agent.district = request.POST.get('district')

        # Update profile image if uploaded
        if request.FILES.get('profile_image'):
            agent.profile_image = request.FILES.get('profile_image')

        agent.save()
        messages.success(request, "Agent updated successfully")
        return redirect('view_agent')

    return render(request, 'edit_agent.html', {'agent': agent})

def delete_agent(request, id):
    agent = get_object_or_404(Agent, id=id)
    agent.delete()
    messages.success(request, "Agent deleted successfully")
    return redirect('view_agent')

def add_campaign(request):
    agents = Agent.objects.all()

    if request.method == "POST":
        name = request.POST.get('name')
        agent_id = request.POST.get('agent')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        location = request.POST.get('location')

        # 🔴 Campaign name already exists check
        if Campaign.objects.filter(name__iexact=name).exists():
            messages.error(request, "Campaign name already exists ❌")
            return redirect('add_campaign')

        # ✅ If not exists, create campaign
        Campaign.objects.create(
            name=name,
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date,
            location=location
        )

        messages.success(request, "Campaign added successfully ")
        return redirect('add_campaign')

    return render(request, 'add_campaign.html', {'agents': agents})

def view_campaign(request):
    campaigns = Campaign.objects.all().order_by('-created_at')
    return render(request, 'view_campaign.html', {'campaigns': campaigns})

def edit_campaign(request, id):
    campaign = get_object_or_404(Campaign, id=id)
    agents = Agent.objects.all()

    if request.method == "POST":
        name = request.POST.get('name')

        if Campaign.objects.filter(name__iexact=name).exclude(id=id).exists():
            messages.error(request, "Campaign name already exists ❌")
            return redirect('edit_campaign', id=id)

        campaign.name = name
        campaign.agent_id = request.POST.get('agent')
        campaign.start_date = request.POST.get('start_date')
        campaign.end_date = request.POST.get('end_date')
        campaign.location = request.POST.get('location')
        campaign.save()

        messages.success(request, "Campaign updated successfully")
        return redirect('view_campaign')

    return render(request, 'edit_campaign.html', {
        'campaign': campaign,
        'agents': agents
    })


def delete_campaign(request, id):
    campaign = get_object_or_404(Campaign, id=id)
    campaign.delete()
    messages.success(request, "Campaign deleted successfully ")
    return redirect('view_campaign')

def client_view(request):
    clients = Client.objects.select_related("campaign", "agent").order_by("-created_at")
    return render(request, "client_view.html", {"clients": clients})


def add_client(request):
    agent_id = request.session.get("agent_id")

    # 🔒 SAFETY CHECK
    if not agent_id:
        messages.error(request, "Please login again.")
        return redirect("agent_login")

    agent = Agent.objects.filter(id=agent_id).first()

    if not agent:
        messages.error(request, "Invalid agent session.")
        return redirect("agent_login")

    # ✅ ONLY THIS AGENT'S CAMPAIGNS
    campaigns = Campaign.objects.filter(agent=agent)

    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        aadhaar_number = request.POST.get("aadhaar_number")

        # ✅ CHECK DUPLICATE CLIENT FOR SAME AGENT
        existing_client = Client.objects.filter(
            agent=agent,
            phone=phone
        ).first()

        if existing_client:
            messages.error(request, "Client with this phone number already exists.")
        else:
            Client.objects.create(
                agent=agent,
                campaign_id=request.POST.get("campaign") or None,

                name=name,
                phone=phone,
                address=request.POST.get("address"),
                dob=request.POST.get("dob"),
                age=request.POST.get("age"),

                qualification=request.POST.get("qualification"),
                profession=request.POST.get("profession"),

                aadhaar_number=aadhaar_number,
                pan_number=request.POST.get("pan_number"),

                income_level=request.POST.get("income_level"),
                marital_status=request.POST.get("marital_status"),
                has_kids=request.POST.get("has_kids") == "True",
                referral_source=request.POST.get("referral_source"),
                existing_policy=request.POST.get("existing_policy") == "True",
                service_satisfaction=request.POST.get("service_satisfaction"),

                visited_policy=request.POST.get("visited_policy"),
                willing_to_purchase=request.POST.get("willing_to_purchase") == "True",
                willing_to_switch=request.POST.get("willing_to_switch") == "True",
                willing_to_share_previous=request.POST.get("willing_to_share_previous") == "True",

                previous_policy_number=request.POST.get("previous_policy_number"),
                previous_policy_name=request.POST.get("previous_policy_name"),
                previous_claimed=request.POST.get("previous_claimed") == "True",

                customer_preferences=request.POST.get("customer_preferences"),
                agent_note=request.POST.get("agent_note"),
            )

            messages.success(request, "Client added successfully")
            return redirect("add_client")

    return render(
        request,
        "add_client.html",
        {
            "campaigns": campaigns,
            "agent": agent
        }
    )

def check_client_exists(request):
    agent_id = request.session.get("agent_id")

    # 🔒 session safety
    if not agent_id:
        return JsonResponse({"exists": False})

    agent = Agent.objects.filter(id=agent_id).first()
    if not agent:
        return JsonResponse({"exists": False})

    field = request.GET.get("field")
    value = request.GET.get("value")
    client_id = request.GET.get("client_id")  # 👈 EDIT support

    qs = Client.objects.filter(agent=agent)

    # 👇 EDIT page case → ignore current client
    if client_id:
        qs = qs.exclude(id=client_id)

    exists = False

    if field == "phone":
        exists = qs.filter(phone=value).exists()

    elif field == "aadhaar_number":
        exists = qs.filter(aadhaar_number=value).exists()

    elif field == "pan_number":
        exists = qs.filter(pan_number=value).exists()

    return JsonResponse({"exists": exists})


def client_card_view(request):
    agent_id = request.session.get("agent_id")
    agent = Agent.objects.filter(id=agent_id).first() if agent_id else None

    if agent:
        # only fetch clients for this agent
        clients = Client.objects.filter(agent=agent).order_by("-created_at")
    else:
        clients = Client.objects.none()

    return render(request, "client_card_view.html", {"clients": clients})


def edit_client(request, id):
    client = get_object_or_404(Client, id=id)

    # 🔹 Logged-in agent
    agent_id = request.session.get("agent_id")
    agent = Agent.objects.filter(id=agent_id).first()

    # 🔹 Only campaigns assigned to this agent
    campaigns = Campaign.objects.filter(agent=agent)

    if request.method == "POST":
        client.name = request.POST.get("name")
        client.phone = request.POST.get("phone")
        client.address = request.POST.get("address")
        client.dob = request.POST.get("dob")
        client.age = request.POST.get("age")

        client.qualification = request.POST.get("qualification")
        client.profession = request.POST.get("profession")

        client.aadhaar_number = request.POST.get("aadhaar_number")
        client.pan_number = request.POST.get("pan_number")

        client.income_level = request.POST.get("income_level")
        client.marital_status = request.POST.get("marital_status")
        client.has_kids = request.POST.get("has_kids") == "True"

        client.referral_source = request.POST.get("referral_source")
        client.existing_policy = request.POST.get("existing_policy") == "True"
        client.service_satisfaction = request.POST.get("service_satisfaction")

        # 🔹 campaign also from agent-specific list
        client.campaign_id = request.POST.get("campaign") or None

        client.visited_policy = request.POST.get("visited_policy")
        client.willing_to_purchase = request.POST.get("willing_to_purchase") == "True"
        client.willing_to_switch = request.POST.get("willing_to_switch") == "True"
        client.willing_to_share_previous = request.POST.get("willing_to_share_previous") == "True"

        client.previous_policy_number = request.POST.get("previous_policy_number")
        client.previous_policy_name = request.POST.get("previous_policy_name")
        client.previous_claimed = request.POST.get("previous_claimed") == "True"

        client.customer_preferences = request.POST.get("customer_preferences")
        client.agent_note = request.POST.get("agent_note")

        client.save()

        messages.success(request, "Client Details Updated Successfully")
        return redirect("client_card_view")

    return render(
        request,
        "edit_client.html",
        {
            "client": client,
            "campaigns": campaigns
        }
    )

def delete_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    client.delete()
    messages.success(request, f"Client '{client.name}' deleted successfully.")
    return redirect('client_card_view')


def view_campaignlist(request):

    if not request.session.get("agent_id"):
        return redirect("loginpage")

    agent_id = request.session["agent_id"  ]

    campaigns = Campaign.objects.filter(
        agent_id=agent_id
    ).order_by('-created_at')

    return render(request, 'view_campaignlist.html', {
        'campaigns': campaigns
    })


def agent_profile_view(request):
    # Get logged-in agent from session
    agent_id = request.session.get("agent_id")
    if not agent_id:
        messages.error(request, "Please login first")
        return redirect("loginpage")

    try:
        agent = Agent.objects.get(id=agent_id)
    except Agent.DoesNotExist:
        messages.error(request, "Agent not found")
        return redirect("loginpage")

    return render(request, "agent_profile_view.html", {"agent": agent})


def agent_profile_edit(request):
    agent_id = request.session.get("agent_id")
    if not agent_id:
        messages.error(request, "Please login first")
        return redirect("loginpage")

    try:
        agent = Agent.objects.get(id=agent_id)
    except Agent.DoesNotExist:
        messages.error(request, "Agent not found")
        return redirect("loginpage")

    if request.method == "POST":
        agent.first_name = request.POST.get("first_name")
        agent.last_name = request.POST.get("last_name")
        agent.username = request.POST.get("username")
        agent.email = request.POST.get("email")
        agent.phone = request.POST.get("phone")
        agent.age = request.POST.get("age") or None
        agent.qualification = request.POST.get("qualification")
        agent.address = request.POST.get("address")
        agent.city = request.POST.get("city")
        agent.district = request.POST.get("district")

        # Update profile image if uploaded
        if request.FILES.get("profile_image"):
            agent.profile_image = request.FILES.get("profile_image")

        agent.save()
        messages.success(request, "Profile updated successfully")
        return redirect("agent_profile_view")

    return render(request, "agent_profile_edit.html", {"agent": agent})

def validate_agent_unique_field(request):
    field = request.GET.get("field")
    value = request.GET.get("value")
    agent_id = request.GET.get("agent_id")

    qs = Agent.objects.filter(**{field: value})

    # Edit page il current agent exclude cheyyan
    if agent_id:
        qs = qs.exclude(id=agent_id)

    return JsonResponse({"exists": qs.exists()})

def resetpage(request):
    return render(request,'resetpage.html')

def reset_password_fun(request):
    if not request.session.get("agent_id"):
        return redirect("loginpage")

    if request.method == "POST":
        current_password = request.POST.get("currentpass", "").strip()
        new_password = request.POST.get("newpass", "").strip()
        confirm_password = request.POST.get("confirmpass", "").strip()

        agent = Agent.objects.get(id=request.session["agent_id"])

        # 1️⃣ Empty fields
        if not current_password or not new_password or not confirm_password:
            messages.error(request, "All fields required aanu")
            return redirect("resetpage")

        # 2️⃣ Current password check
        if not check_password(current_password, agent.password):
            messages.error(request, "Current password is incorrect")
            return redirect("resetpage")

        # 3️⃣ New password same as old
        if check_password(new_password, agent.password):
            messages.error(request, "New password should not be like current password")
            return redirect("resetpage")

        # 4️⃣ Confirm password match
        if new_password != confirm_password:
            messages.error(request, "New passwords are not matched")
            return redirect("resetpage")

        # 5️⃣ Length check
        if len(new_password) < 8:
            messages.error(
                request,
                "Password must be at least 8 characters long and contain at least one uppercase letter, one digit, and one special character."
            )
            return redirect("resetpage")

        # 6️⃣ Strong password validation
        pattern = r'^(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$'
        if not re.match(pattern, new_password):
            messages.error(
                request,
                "Password must be at least 8 characters long and contain at least one uppercase letter, one digit, and one special character."
            )
            return redirect("resetpage")

        # ✅ Save hashed password
        agent.password = make_password(new_password)
        agent.save()

        messages.success(request, "Password successfully changed")
        return redirect("loginpage")

    return render(request, "resetpage.html")