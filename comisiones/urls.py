from django.urls import path

from . import views

urlpatterns = [
    path("", views.comisiones_lista, name="comisiones_comision_list"),
    path("detalle/<int:comisionista_id>/", views.comisiones_detalle, name="comisiones_comisionista_detail"),
    path("detalle/<int:comisionista_id>/enviar/", views.enviar_detalle_comisionista, name="comisiones_comisionista_send"),
    path("pago/nuevo/<int:comisionista_id>/", views.registrar_pago, name="comisiones_pagocomision_create_for_comisionista"),
    path("pago/nuevo/", views.registrar_pago, name="comisiones_pagocomision_create"),
    path("pago/editar/<int:id>/", views.editar_pago, name="comisiones_pagocomision_update"),
    path("pago/eliminar/<int:id>/", views.eliminar_pago, name="comisiones_pagocomision_delete"),
]
