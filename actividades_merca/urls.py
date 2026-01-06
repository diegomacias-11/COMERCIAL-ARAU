from django.urls import path

from . import views

urlpatterns = [
    path("", views.actividades_lista, name="actividades_merca_lista"),
    path("nueva/", views.crear_actividad, name="actividades_merca_crear"),
    path("<int:pk>/", views.editar_actividad, name="actividades_merca_editar"),
    path("<int:pk>/eliminar/", views.eliminar_actividad, name="actividades_merca_eliminar"),
    path("solicitud/", views.solicitud_publica, name="actividades_merca_solicitud_publica"),
]
