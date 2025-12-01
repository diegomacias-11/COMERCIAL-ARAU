from django.shortcuts import render, redirect


def inicio(request):
    return render(request, 'base.html')


def root_redirect(request):
    """Entra al login si no está autenticado; si ya inició, va a la lista de citas."""
    if request.user.is_authenticated:
        return redirect('citas_lista')
    return redirect('login')
