from django.db import models
from django.utils import timezone

class Attendance(models.Model):
    mac_address = models.CharField(max_length=17, unique=True, db_index=True)
    device_name = models.CharField(max_length=100, blank=True, null=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-last_seen']
        verbose_name = 'Device Attendance'
        verbose_name_plural = 'Device Attendance Records'
    
    def __str__(self):
        return f"{self.mac_address} - {self.device_name or 'Unknown Device'}"
    
    @property
    def time_since_last_seen(self):
        """Returns human-readable time since last seen"""
        from django.utils.timesince import timesince
        return timesince(self.last_seen)
    
    def mark_as_active(self):
        """Mark device as currently active"""
        self.last_seen = timezone.now()
        self.is_active = True
        self.save()
    
    def mark_as_inactive(self):
        """Mark device as inactive"""
        self.is_active = False
        self.save()