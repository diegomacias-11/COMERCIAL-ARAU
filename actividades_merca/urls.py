from django.urls import path

from . import views

urlpatterns = [
    path("", views.actividades_lista, name="actividades_merca_actividad_list"),
    path("reporte/", views.reporte_actividades, name="actividades_merca_actividad_report"),
    path("nueva/", views.crear_actividad, name="actividades_merca_actividad_create"),
    path("<int:pk>/", views.editar_actividad, name="actividades_merca_actividad_update"),
    path("<int:pk>/eliminar/", views.eliminar_actividad, name="actividades_merca_actividad_delete"),
    path("solicitud/", views.solicitud_publica, name="actividades_merca_solicitud_publica"),
]
