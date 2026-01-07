from django.urls import path

from . import views

urlpatterns = [
    path("", views.actividades_exp_lista, name="actividades_exp_lista"),
    path("kanban/", views.actividades_exp_kanban, name="actividades_exp_kanban"),
    path("nueva/", views.crear_actividad_exp, name="actividades_exp_crear"),
    path("<int:pk>/", views.editar_actividad_exp, name="actividades_exp_editar"),
    path("<int:pk>/eliminar/", views.eliminar_actividad_exp, name="actividades_exp_eliminar"),
]
