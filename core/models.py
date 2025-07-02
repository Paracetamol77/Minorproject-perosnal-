from django.db import models

class Routine(models.Model):
    subject = models.CharField(max_length=100)
    day = models.CharField(max_length=20)
    time = models.TimeField()

    def __str__(self):
        return f"{self.subject} on {self.day} at {self.time}"

class Attendance(models.Model):
    date = models.DateField()
    status = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.date} - {self.status}"

class Note(models.Model):
    title = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
