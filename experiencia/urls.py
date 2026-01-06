from django.urls import path

from . import views

urlpatterns = [
    path("clientes/", views.clientes_experiencia_lista, name="clientes_experiencia_lista"),
    path("clientes/<int:pk>/", views.editar_cliente_experiencia, name="editar_cliente_experiencia"),
]
