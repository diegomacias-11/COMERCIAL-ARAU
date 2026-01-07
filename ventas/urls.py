from django.urls import path

from . import views

urlpatterns = [
    path("", views.ventas_lista, name="ventas_venta_list"),
    path("nueva/", views.agregar_venta, name="ventas_venta_create"),
    path("editar/<int:id>/", views.editar_venta, name="ventas_venta_update"),
    path("eliminar/<int:id>/", views.eliminar_venta, name="ventas_venta_delete"),
]
