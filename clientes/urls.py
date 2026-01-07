from django.urls import path
from . import views

urlpatterns = [
    path("", views.clientes_lista, name="clientes_cliente_list"),
    path("agregar/", views.agregar_cliente, name="clientes_cliente_create"),
    path("<int:id>/", views.editar_cliente, name="clientes_cliente_update"),
    path("<int:id>/contactos/", views.contactos_cliente, name="clientes_contacto_list"),
    path("contactos/<int:id>/eliminar/", views.eliminar_contacto, name="clientes_contacto_delete"),
    path("<int:id>/eliminar/", views.eliminar_cliente, name="clientes_cliente_delete"),
]
