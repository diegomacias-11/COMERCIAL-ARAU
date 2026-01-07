from django.urls import path
from . import views

urlpatterns = [
    path("", views.alianzas_lista, name="alianzas_alianza_list"),
    path("agregar/", views.agregar_alianzas, name="alianzas_alianza_create"),
    path("<int:id>/", views.editar_alianzas, name="alianzas_alianza_update"),
    path("<int:id>/eliminar/", views.eliminar_alianzas, name="alianzas_alianza_delete"),
]

