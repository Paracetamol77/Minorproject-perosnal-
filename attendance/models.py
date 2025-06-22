from django.db import models

class Attendance(models.Model):
    mac_address = models.CharField(max_length=17, unique=True)  # MAC format XX:XX:XX:XX:XX:XX
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.mac_address
