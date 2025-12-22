from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class UserSessionActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="session_activities")
    session_key = models.CharField(max_length=64, db_index=True, unique=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Actividad de sesión"
        verbose_name_plural = "Actividades de sesión"

    def __str__(self):
        return f"{self.user} - {self.last_seen}"
