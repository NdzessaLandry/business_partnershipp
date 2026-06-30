from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Entreprise, BesoinOffreEntreprise, Service, REGIONS_CAMEROUN, BRANCHES_ACTIVITE


class InscriptionForm(UserCreationForm):
    raison_sociale = forms.CharField(max_length=255, label="Raison sociale")
    email = forms.EmailField(label="Adresse email")
    est_locale = forms.ChoiceField(
        choices=[('True', 'Locale (Cameroun)'), ('False', 'Étrangère')],
        label="Caractère de l'entreprise",
        widget=forms.RadioSelect
    )
    region = forms.ChoiceField(choices=[('', '-- Sélectionner --')] + REGIONS_CAMEROUN, required=False, label="Région")
    branche_activite = forms.ChoiceField(choices=[('', '-- Sélectionner --')] + BRANCHES_ACTIVITE, label="Branche d'activité")
    doc_registre_commerce = forms.FileField(label="Registre de commerce")
    doc_contribuable = forms.FileField(label="Carte de contribuable")
    doc_autre = forms.FileField(label="Document complémentaire (facultatif)", required=False)

    class Meta:
        model = Entreprise
        fields = ['username', 'raison_sociale', 'email', 'password1', 'password2',
                  'est_locale', 'region', 'branche_activite',
                  'doc_registre_commerce', 'doc_contribuable', 'doc_autre']

    def clean(self):
        cleaned = super().clean()
        est_locale = cleaned.get('est_locale')
        region = cleaned.get('region')
        if est_locale == 'True' and not region:
            self.add_error('region', "La région est obligatoire pour une entreprise locale.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.est_locale = self.cleaned_data['est_locale'] == 'True'
        if commit:
            user.save()
        return user


class ConnexionForm(AuthenticationForm):
    username = forms.CharField(label="Nom d'utilisateur")
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")


class ProfilForm(forms.ModelForm):
    class Meta:
        model = Entreprise
        fields = ['raison_sociale', 'email', 'est_locale', 'region', 'branche_activite', 'description']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}


class ServiceChoiceForm(forms.Form):
    """Formulaire dynamique pour sélectionner les éléments d'un service."""
    nom_service = forms.ChoiceField(label="Service", widget=forms.Select(attrs={'id': 'id_nom_service'}))
    elements = forms.ModelMultipleChoiceField(
        queryset=Service.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        label="Éléments du service"
    )
    type_relation = forms.ChoiceField(
        choices=[('besoin', 'Besoin'), ('offre', 'Offre')],
        widget=forms.RadioSelect,
        label="Type"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        noms = Service.objects.values_list('nom_service', flat=True).distinct()
        self.fields['nom_service'].choices = [('', '-- Choisir un service --')] + [(n, n) for n in noms]
