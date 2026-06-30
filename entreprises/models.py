from django.contrib.auth.models import AbstractUser
from django.db import models


REGIONS_CAMEROUN = [
    ('Adamaoua', 'Adamaoua'), ('Centre', 'Centre'), ('Est', 'Est'),
    ('Extreme-Nord', 'Extrême-Nord'), ('Littoral', 'Littoral'), ('Nord', 'Nord'),
    ('Nord-Ouest', 'Nord-Ouest'), ('Ouest', 'Ouest'), ('Sud', 'Sud'), ('Sud-Ouest', 'Sud-Ouest'),
]

STATUT_CHOICES = [
    ('EN_ATTENTE', 'En attente de validation'),
    ('APPROUVEE', 'Approuvée'),
    ('REJETEE', 'Rejetée'),
]

BRANCHES_ACTIVITE = [
    ('Agriculture', 'Agriculture & Agroalimentaire'),
    ('BTP', 'BTP & Construction'),
    ('Commerce', 'Commerce & Distribution'),
    ('Energie', 'Énergie & Mines'),
    ('Finance', 'Finance & Assurance'),
    ('Industrie', 'Industrie & Manufacture'),
    ('Numerique', 'Numérique & Télécoms'),
    ('Sante', 'Santé & Pharmaceutique'),
    ('Services', 'Services aux entreprises'),
    ('Transport', 'Transport & Logistique'),
    ('Autre', 'Autre'),
]


class Entreprise(AbstractUser):
    raison_sociale = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    est_locale = models.BooleanField(default=True)
    region = models.CharField(max_length=50, choices=REGIONS_CAMEROUN, blank=True, null=True)
    branche_activite = models.CharField(max_length=50, choices=BRANCHES_ACTIVITE, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    date_inscription = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(blank=True, null=True)
    motif_rejet = models.TextField(blank=True, null=True)
    doc_registre_commerce = models.FileField(upload_to='documents/')
    doc_contribuable = models.FileField(upload_to='documents/')
    doc_autre = models.FileField(upload_to='documents/', blank=True, null=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'raison_sociale']

    class Meta:
        verbose_name = "Entreprise"

    def __str__(self):
        return self.raison_sociale

    def is_approved(self):
        return self.statut == 'APPROUVEE'


class Service(models.Model):
    nom_service = models.CharField(max_length=150)
    element = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['nom_service', 'element']

    def __str__(self):
        return f"{self.nom_service} — {self.element}"


class BesoinOffreEntreprise(models.Model):
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='besoins_offres')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='besoins_offres')
    besoin = models.BooleanField(default=True)
    date_enregistrement = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('entreprise', 'service', 'besoin')

    def __str__(self):
        t = "Besoin" if self.besoin else "Offre"
        return f"{self.entreprise.raison_sociale} | {t} | {self.service}"
