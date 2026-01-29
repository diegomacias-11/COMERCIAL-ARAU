from django.urls import path
from . import views

urlpatterns = [
    path("kpis/", views.comercial_kpis, name="comercial_kpis"),
    path("citas/", views.citas_lista, name="comercial_cita_list"),
    path("citas/kanban/", views.citas_kanban, name="comercial_cita_kanban"),
    path("citas/kanban/resumen/", views.citas_kanban_resumen_pdf, name="comercial_cita_kanban_resumen"),
    path("citas/agregar/", views.agregar_cita, name="comercial_cita_create"),
    path("citas/<int:id>/", views.editar_cita, name="comercial_cita_update"),
    path("citas/<int:id>/eliminar/", views.eliminar_cita, name="comercial_cita_delete"),
]
