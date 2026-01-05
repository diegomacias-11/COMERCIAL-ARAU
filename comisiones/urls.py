from django.urls import path

from . import views

urlpatterns = [
    path("", views.comisiones_lista, name="comisiones_lista"),
    path("detalle/<int:comisionista_id>/", views.comisiones_detalle, name="comisiones_detalle"),
    path("detalle/<int:comisionista_id>/enviar/", views.enviar_detalle_comisionista, name="comisiones_enviar_detalle"),
    path("pago/nuevo/<int:comisionista_id>/", views.registrar_pago, name="comisiones_registrar_pago_by_id"),
    path("pago/nuevo/", views.registrar_pago, name="comisiones_registrar_pago"),
    path("pago/editar/<int:id>/", views.editar_pago, name="comisiones_editar_pago"),
    path("pago/eliminar/<int:id>/", views.eliminar_pago, name="comisiones_eliminar_pago"),
]
