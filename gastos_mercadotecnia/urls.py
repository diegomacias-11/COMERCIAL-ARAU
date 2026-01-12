from django.urls import path

from . import views

urlpatterns = [
    path("", views.gastos_lista, name="gastos_mercadotecnia_gasto_list"),
    path("reporte/", views.reporte_gastos, name="gastos_mercadotecnia_gasto_report"),
    path("nuevo/", views.gastos_crear, name="gastos_mercadotecnia_gasto_create"),
    path("<int:pk>/", views.gastos_editar, name="gastos_mercadotecnia_gasto_update"),
]
