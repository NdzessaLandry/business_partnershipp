import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from .models import Entreprise, Service, BesoinOffreEntreprise
from .forms import InscriptionForm, ConnexionForm, ProfilForm


def inscription(request):
    if request.method == 'POST':
        form = InscriptionForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre demande a été enregistrée. Elle sera examinée par les équipes du ministère.")
            return redirect('connexion')
    else:
        form = InscriptionForm()
    return render(request, 'entreprises/inscription.html', {'form': form})


def connexion(request):
    if request.user.is_authenticated and not request.user.is_staff:
        return redirect('dashboard')
    from django.contrib.auth.forms import AuthenticationForm
    if request.method == 'POST':
        form = ConnexionForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not user.is_staff and user.statut != 'APPROUVEE':
                messages.error(request, "Votre compte est en attente de validation ou a été rejeté.")
                return redirect('connexion')
            login(request, user)
            return redirect('dashboard')
        messages.error(request, "Identifiants incorrects.")
    else:
        form = ConnexionForm()
    return render(request, 'entreprises/connexion.html', {'form': form})


def deconnexion(request):
    logout(request)
    return redirect('connexion')


@login_required
def dashboard(request):
    entreprise = request.user
    mes_besoins = BesoinOffreEntreprise.objects.filter(entreprise=entreprise, besoin=True).select_related('service')
    mes_offres  = BesoinOffreEntreprise.objects.filter(entreprise=entreprise, besoin=False).select_related('service')
    ids_besoins = mes_besoins.values_list('service_id', flat=True)
    partenaires = []
    if ids_besoins:
        partenaires = (
            Entreprise.objects
            .filter(besoins_offres__service__in=ids_besoins, besoins_offres__besoin=False, statut='APPROUVEE')
            .exclude(pk=entreprise.pk)
            .annotate(nb_correspondances=Count('besoins_offres__service',
                      filter=Q(besoins_offres__service__in=ids_besoins, besoins_offres__besoin=False)))
            .order_by('-nb_correspondances')
            .distinct()
        )
    return render(request, 'entreprises/dashboard.html', {
        'entreprise': entreprise,
        'mes_besoins': mes_besoins,
        'mes_offres': mes_offres,
        'partenaires': partenaires,
    })


@login_required
def profil(request):
    if request.method == 'POST':
        form = ProfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour.")
            return redirect('profil')
    else:
        form = ProfilForm(instance=request.user)
    return render(request, 'entreprises/profil.html', {'form': form})


@login_required
def gerer_services(request, type_relation):
    est_besoin = (type_relation == 'besoins')
    label = "besoins" if est_besoin else "offres"
    relations_actuelles = BesoinOffreEntreprise.objects.filter(
        entreprise=request.user, besoin=est_besoin
    ).select_related('service')
    noms = list(Service.objects.values_list('nom_service', flat=True).distinct().order_by('nom_service'))
    return render(request, 'entreprises/gerer_services.html', {
        'type_relation': type_relation,
        'label': label,
        'est_besoin': est_besoin,
        'relations_actuelles': relations_actuelles,
        'service_names': json.dumps(noms),
    })


@login_required
def enregistrer_service(request):
    if request.method == 'POST':
        ids = request.POST.getlist('elements')
        est_besoin = request.POST.get('type_relation') == 'besoin'
        for sid in ids:
            service = get_object_or_404(Service, pk=sid)
            BesoinOffreEntreprise.objects.get_or_create(
                entreprise=request.user, service=service, besoin=est_besoin
            )
        messages.success(request, "Services enregistrés avec succès.")
        return redirect('gerer_services', type_relation='besoins' if est_besoin else 'offres')
    return redirect('dashboard')


@login_required
def supprimer_service(request, pk):
    relation = get_object_or_404(BesoinOffreEntreprise, pk=pk, entreprise=request.user)
    est_besoin = relation.besoin
    relation.delete()
    messages.success(request, "Service supprimé.")
    return redirect('gerer_services', type_relation='besoins' if est_besoin else 'offres')


@login_required
def fiche_entreprise(request, pk):
    ent = get_object_or_404(Entreprise, pk=pk, statut='APPROUVEE')
    offres  = BesoinOffreEntreprise.objects.filter(entreprise=ent, besoin=False).select_related('service')
    besoins = BesoinOffreEntreprise.objects.filter(entreprise=ent, besoin=True).select_related('service')
    return render(request, 'entreprises/fiche_entreprise.html', {'ent': ent, 'offres': offres, 'besoins': besoins})


def api_elements_service(request):
    nom = request.GET.get('nom_service', '')
    elements = list(Service.objects.filter(nom_service=nom).values('id', 'element', 'description'))
    return JsonResponse({'elements': elements})
