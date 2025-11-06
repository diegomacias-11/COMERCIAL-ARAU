from django.urls import path
from . import views

urlpatterns = [
    path("citas/", views.citas_lista, name="citas_lista"),
    path("citas/agregar/", views.agregar_cita, name="agregar_cita"),
    path("citas/<int:id>/", views.editar_cita, name="editar_cita"),
    path("citas/<int:id>/eliminar/", views.eliminar_cita, name="eliminar_cita"),
]
