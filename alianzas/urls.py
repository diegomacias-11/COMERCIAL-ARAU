from django.urls import path
from . import views

urlpatterns = [
    path("alianzas/", views.alianzas_lista, name="alianzas_lista"),
    path("alianzas/agregar/", views.agregar_alianzas, name="agregar_alianzas"),
    path("alianzas/<int:id>/", views.editar_alianzas, name="editar_alianzas"),
    path("alianzas/<int:id>/eliminar/", views.eliminar_alianzas, name="eliminar_alianzas"),
]

