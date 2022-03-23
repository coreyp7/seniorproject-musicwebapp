from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class UserToken(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
    )
    token = models.TextField()
