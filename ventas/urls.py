from django.urls import path

from . import views

urlpatterns = [
    path("", views.ventas_lista, name="ventas_lista"),
    path("nueva/", views.agregar_venta, name="ventas_agregar"),
    path("editar/<int:id>/", views.editar_venta, name="ventas_editar"),
    path("eliminar/<int:id>/", views.eliminar_venta, name="ventas_eliminar"),
]
