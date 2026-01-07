from django.urls import path

from . import views

urlpatterns = [
    path("", views.actividades_exp_lista, name="actividades_exp_actividadexp_list"),
    path("kanban/", views.actividades_exp_kanban, name="actividades_exp_actividadexp_kanban"),
    path("nueva/", views.crear_actividad_exp, name="actividades_exp_actividadexp_create"),
    path("<int:pk>/", views.editar_actividad_exp, name="actividades_exp_actividadexp_update"),
    path("<int:pk>/eliminar/", views.eliminar_actividad_exp, name="actividades_exp_actividadexp_delete"),
]
