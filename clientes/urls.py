from django.urls import path
from . import views

urlpatterns = [
    path("clientes/", views.clientes_lista, name="clientes_lista"),
    path("clientes/agregar/", views.agregar_cliente, name="agregar_cliente"),
    path("clientes/<int:id>/", views.editar_cliente, name="editar_cliente"),
    path("clientes/<int:id>/eliminar/", views.eliminar_cliente, name="eliminar_cliente"),
]

