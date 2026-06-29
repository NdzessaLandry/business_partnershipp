# Business Partnership — MINEPAT
## Plateforme gouvernementale de mise en relation des entreprises

### Prérequis
- Python 3.10+
- pip

### Installation

```bash
# 1. Cloner / décompresser le projet
cd business_partnership

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate

# 3. Installer les dépendances
pip install django pillow

# 4. Appliquer les migrations
python manage.py migrate

# 5. Charger les services initiaux
python manage.py loaddata entreprises/fixtures/services.json

# 6. Créer un agent ministère (staff)
python manage.py createsuperuser

# 7. Lancer le serveur
python manage.py runserver
```

### Accès
| Rôle | URL | Identifiants (démo) |
|------|-----|----------------------|
| Agent ministère | /ministere/ | admin_minepat / Admin2025! |
| Entreprise | /dashboard/ | (après validation) |
| Admin Django | /admin/ | admin_minepat / Admin2025! |

### Architecture

```
business_partnership/
├── business_partnership_proj/   # Configuration Django
├── entreprises/                 # App principale
│   ├── models.py               # Entreprise (AbstractUser), Service, BesoinOffreEntreprise
│   ├── views.py                # Vues entreprise + API JSON
│   ├── forms.py                # Formulaires
│   ├── admin.py                # Interface admin
│   └── fixtures/services.json  # 31 éléments de services initiaux
├── ministere/                   # App validation
│   └── views.py                # Tableau de bord, examen des demandes
├── templates/                   # Templates HTML
│   ├── base.html               # Layout commun
│   ├── entreprises/            # Pages entreprise
│   └── ministere/              # Pages agent
├── static/
│   ├── css/style.css           # Charte graphique institutionnelle
│   └── js/app.js
└── media/                       # Documents téléversés
```

### Modèle dimensionnel

**Dimension Service** (`service`) : chaque ligne = un élément d'un service
```
id | nom_service                    | element              | description
 1 | Fourniture d'équipements...    | Machines industrielles|
 2 | Fourniture d'équipements...    | Outillage            |
```

**Table de faits** (`besoin_offre_entreprise`) :
```
id | entreprise_id | service_id | besoin
 1 |      5        |     8      | True   → Entreprise 5 a besoin d'emballage plastique
 2 |      3        |     8      | False  → Entreprise 3 offre l'emballage plastique
```

**Algorithme de mise en relation** :
```sql
SELECT entreprise, COUNT(service) AS nb_correspondances
FROM besoin_offre_entreprise
WHERE service IN (mes_besoins) AND besoin = False
AND entreprise != moi AND statut = 'APPROUVEE'
GROUP BY entreprise
ORDER BY nb_correspondances DESC
```

### Flux utilisateur
1. L'entreprise soumet sa demande avec 3 documents
2. L'agent ministère examine les documents → approuve ou rejette avec motif
3. L'entreprise approuvée se connecte et accède à son tableau de bord
4. Elle définit ses besoins et/ou ses offres par service et éléments
5. La plateforme affiche les partenaires potentiels classés par pertinence
6. Elle peut consulter la fiche complète de chaque partenaire

### Charte graphique
- Bleu institutionnel (#1A3A5C) — navbar, boutons principaux
- Bleu ardoise (#2E5077) — accents
- Fond gris-bleu clair (#EEF3F8)
- Typographie système sans-serif
- Aucun emoji — icônes Bootstrap Icons exclusivement
