from django.urls import path

from . import views

urlpatterns = [
    path("clientes/", views.clientes_experiencia_lista, name="experiencia_experienciacliente_list"),
    path("clientes/<int:pk>/", views.editar_cliente_experiencia, name="experiencia_experienciacliente_update"),
]
