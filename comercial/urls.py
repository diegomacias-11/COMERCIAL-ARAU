from django.urls import path
from . import views

urlpatterns = [
    path("citas/", views.citas_lista, name="comercial_cita_list"),
    path("citas/agregar/", views.agregar_cita, name="comercial_cita_create"),
    path("citas/<int:id>/", views.editar_cita, name="comercial_cita_update"),
    path("citas/<int:id>/eliminar/", views.eliminar_cita, name="comercial_cita_delete"),
    path("reportes/", views.reportes_dashboard, name="comercial_reportes_dashboard"),
]
