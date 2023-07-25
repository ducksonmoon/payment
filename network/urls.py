from django.urls import path
from . import views


urlpatterns = [path("trigger/", views.Trigger.as_view(), name="trigger")]
