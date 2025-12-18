from django.urls import path

from . import views

urlpatterns = [
    path("actividades_merca/", views.actividades_lista, name="actividades_merca_lista"),
    path("actividades_merca/nueva/", views.crear_actividad, name="actividades_merca_crear"),
    path("actividades_merca/<int:pk>/", views.editar_actividad, name="actividades_merca_editar"),
    path("actividades_merca/<int:pk>/eliminar/", views.eliminar_actividad, name="actividades_merca_eliminar"),
]
