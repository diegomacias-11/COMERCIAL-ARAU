from django.urls import path
from . import views

urlpatterns = [
    path("", views.alianzas_lista, name="alianzas_lista"),
    path("agregar/", views.agregar_alianzas, name="agregar_alianzas"),
    path("<int:id>/", views.editar_alianzas, name="editar_alianzas"),
    path("<int:id>/eliminar/", views.eliminar_alianzas, name="eliminar_alianzas"),
]

