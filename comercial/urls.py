from django.urls import path
from . import views

urlpatterns = [
    path("citas/", views.citas_lista, name="comercial_cita_list"),
    path("citas/kanban/", views.citas_kanban, name="comercial_cita_kanban"),
    path("citas/agregar/", views.agregar_cita, name="comercial_cita_create"),
    path("citas/<int:id>/", views.editar_cita, name="comercial_cita_update"),
    path("citas/<int:id>/eliminar/", views.eliminar_cita, name="comercial_cita_delete"),
    path("reportes/", views.reportes_dashboard, name="comercial_reportes_dashboard"),
    path("control/", views.control_comercial, name="comercial_control"),
    path("control/kpi/crear/", views.comercial_kpi_create, name="comercial_kpi_create"),
    path("control/kpi/<int:pk>/", views.comercial_kpi_update, name="comercial_kpi_update"),
    path("control/kpi/<int:pk>/eliminar/", views.comercial_kpi_delete, name="comercial_kpi_delete"),
    path("control/meta/crear/", views.comercial_meta_create, name="comercial_meta_create"),
    path("control/meta/<int:pk>/", views.comercial_meta_update, name="comercial_meta_update"),
    path("control/meta/<int:pk>/eliminar/", views.comercial_meta_delete, name="comercial_meta_delete"),
]
