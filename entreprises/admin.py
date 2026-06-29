from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Entreprise, Service, BesoinOffreEntreprise

@admin.register(Entreprise)
class EntrepriseAdmin(UserAdmin):
    list_display = ('raison_sociale', 'email', 'branche_activite', 'est_locale', 'statut', 'date_inscription')
    list_filter = ('statut', 'est_locale', 'branche_activite')
    search_fields = ('raison_sociale', 'email')
    fieldsets = UserAdmin.fieldsets + (
        ('Informations entreprise', {'fields': ('raison_sociale', 'est_locale', 'region', 'branche_activite', 'description', 'statut', 'motif_rejet', 'doc_registre_commerce', 'doc_contribuable', 'doc_autre')}),
    )

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('nom_service', 'element')
    list_filter = ('nom_service',)

@admin.register(BesoinOffreEntreprise)
class BesoinOffreAdmin(admin.ModelAdmin):
    list_display = ('entreprise', 'service', 'besoin', 'date_enregistrement')
    list_filter = ('besoin',)
