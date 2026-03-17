from django.db import models



# =================================================
# AGENT PROFILE (Created when Admin adds Agent)
# =================================================
class Agent(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)

    profile_image = models.ImageField(
        upload_to='agent_profiles/',
        blank=True,
        null=True
    )

    age = models.PositiveIntegerField(blank=True, null=True)
    qualification = models.CharField(max_length=100, blank=True)

    phone = models.CharField(max_length=15)
    address = models.TextField(blank=True)

    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)

    joined_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"



class Campaign(models.Model):
    name = models.CharField(max_length=200)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)
    location = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# =================================================
# CLIENT MODEL (Added by Agent)
# =================================================
class Client(models.Model):

    # ---------------------
    # RELATIONS
    # ---------------------
    agent = models.ForeignKey(
        Agent,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # ---------------------
    # BASIC DETAILS
    # ---------------------
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    dob = models.DateField()
    age = models.PositiveIntegerField(null=True, blank=True)
    qualification = models.CharField(max_length=100, blank=True)
    profession = models.CharField(max_length=100, blank=True)

    # ---------------------
    # IDENTITY DETAILS
    # ---------------------
    aadhaar_number = models.CharField(max_length=12)
    pan_number = models.CharField(max_length=10)

    # ---------------------
    # ADDITIONAL DETAILS
    # ---------------------
    income_level = models.CharField(max_length=100)

    MARITAL_CHOICES = (
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Other', 'Other'),
    )
    marital_status = models.CharField(max_length=20, choices=MARITAL_CHOICES)

    has_kids = models.BooleanField(default=False)
    referral_source = models.CharField(max_length=100)
    existing_policy = models.BooleanField(default=False)
    service_satisfaction = models.CharField(max_length=200, blank=True)

    # ---------------------
    # INSURANCE DETAILS
    # ---------------------
    visited_policy = models.CharField(max_length=100)

    willing_to_purchase = models.BooleanField(default=False)
    willing_to_switch = models.BooleanField(default=False)
    willing_to_share_previous = models.BooleanField(default=False)

    previous_policy_number = models.CharField(max_length=100, blank=True)
    previous_policy_name = models.CharField(max_length=100, blank=True)
    previous_claimed = models.BooleanField(default=False)

    # ---------------------
    # SUMMARY
    # ---------------------
    customer_preferences = models.TextField(blank=True)
    agent_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
