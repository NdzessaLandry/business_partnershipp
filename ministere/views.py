from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from entreprises.models import Entreprise, Service, BesoinOffreEntreprise


@staff_member_required
def tableau_de_bord(request):
    en_attente = Entreprise.objects.filter(statut='EN_ATTENTE', is_staff=False).order_by('date_inscription')
    approuvees = Entreprise.objects.filter(statut='APPROUVEE', is_staff=False).count()
    rejetees = Entreprise.objects.filter(statut='REJETEE', is_staff=False).count()
    return render(request, 'ministere/tableau_de_bord.html', {
        'en_attente': en_attente,
        'nb_approuvees': approuvees,
        'nb_rejetees': rejetees,
    })


@staff_member_required
def examiner_entreprise(request, pk):
    entreprise = get_object_or_404(Entreprise, pk=pk, is_staff=False)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approuver':
            entreprise.statut = 'APPROUVEE'
            entreprise.date_validation = timezone.now()
            entreprise.motif_rejet = None
            entreprise.save()
            messages.success(request, f"L'entreprise « {entreprise.raison_sociale} » a été approuvée.")
        elif action == 'rejeter':
            motif = request.POST.get('motif', '').strip()
            if not motif:
                messages.error(request, "Veuillez indiquer un motif de rejet.")
                return redirect('examiner_entreprise', pk=pk)
            entreprise.statut = 'REJETEE'
            entreprise.motif_rejet = motif
            entreprise.save()
            messages.success(request, f"La demande de « {entreprise.raison_sociale} » a été rejetée.")
        return redirect('ministere_tableau')
    return render(request, 'ministere/examiner_entreprise.html', {'entreprise': entreprise})


@staff_member_required
def liste_entreprises(request):
    statut = request.GET.get('statut', '')
    qs = Entreprise.objects.filter(is_staff=False)
    if statut:
        qs = qs.filter(statut=statut)
    return render(request, 'ministere/liste_entreprises.html', {'entreprises': qs, 'statut': statut})
