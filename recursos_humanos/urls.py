from django.urls import path

from . import views

urlpatterns = [
    path("", views.recursos_humanos_home, name="recursos_humanos_home"),
    path("control/", views.recursos_humanos_control, name="recursos_humanos_control"),
    path("control/comercial/", views.recursos_humanos_comercial_control, name="recursos_humanos_comercial_control"),
    path("resumen/", views.recursos_humanos_resumen, name="recursos_humanos_resumen"),
    path("control/comercial/kpi/crear/", views.recursos_humanos_kpi_create, name="recursos_humanos_kpi_create"),
    path("control/comercial/kpi/<int:pk>/", views.recursos_humanos_kpi_update, name="recursos_humanos_kpi_update"),
    path("control/comercial/kpi/<int:pk>/eliminar/", views.recursos_humanos_kpi_delete, name="recursos_humanos_kpi_delete"),
    path("control/comercial/meta/crear/", views.recursos_humanos_meta_create, name="recursos_humanos_meta_create"),
    path("control/comercial/meta/<int:pk>/", views.recursos_humanos_meta_update, name="recursos_humanos_meta_update"),
    path("control/comercial/meta/<int:pk>/eliminar/", views.recursos_humanos_meta_delete, name="recursos_humanos_meta_delete"),
]
