from django.urls import path

from . import views

urlpatterns = [
    path("", views.recursos_humanos_home, name="recursos_humanos_home"),
    path("control/", views.recursos_humanos_control, name="recursos_humanos_control"),
    path("resumen/", views.recursos_humanos_resumen, name="recursos_humanos_resumen"),
]
