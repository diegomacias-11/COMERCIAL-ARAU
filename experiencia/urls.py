from django.urls import path

from . import views

urlpatterns = [
    path("experiencia/clientes/", views.clientes_experiencia_lista, name="clientes_experiencia_lista"),
    path("experiencia/clientes/<int:pk>/", views.editar_cliente_experiencia, name="editar_cliente_experiencia"),
]
