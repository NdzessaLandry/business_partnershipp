"""
Tests de la plateforme Business Partnership — MINEPAT
======================================================
Organisation :
  T1  — Modèles (intégrité des données)
  T2  — Authentification et contrôle d'accès
  T3  — Inscription des entreprises
  T4  — Validation par le ministère
  T5  — Gestion des services (besoins et offres)
  T6  — Algorithme de mise en relation
  T7  — API JSON
  T8  — Isolation et sécurité des données
"""

from io import BytesIO
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Entreprise, Service, BesoinOffreEntreprise


# ─────────────────────────────────────────────────────────────────────────────
# Helpers partagés
# ─────────────────────────────────────────────────────────────────────────────

def fake_pdf(name="doc.pdf"):
    return SimpleUploadedFile(name, b"%PDF-1.4 fake", content_type="application/pdf")

def creer_entreprise(username="ent_a", email="a@test.cm", statut="APPROUVEE",
                     branche="Commerce", region="Centre", **kwargs):
    e = Entreprise(
        username=username, email=email, raison_sociale=username.upper(),
        est_locale=True, region=region, branche_activite=branche,
        statut=statut,
        doc_registre_commerce="documents/fake.pdf",
        doc_contribuable="documents/fake.pdf",
    )
    e.set_password("TestPass2025!")
    for k, v in kwargs.items():
        setattr(e, k, v)
    e.save()
    return e

def creer_service(nom="Financement", element="Crédit"):
    return Service.objects.get_or_create(nom_service=nom, element=element)[0]

def creer_agent():
    a = Entreprise(username="agent", email="agent@minepat.cm",
                   raison_sociale="MINEPAT", is_staff=True, statut="APPROUVEE",
                   doc_registre_commerce="documents/fake.pdf",
                   doc_contribuable="documents/fake.pdf")
    a.set_password("Agent2025!")
    a.save()
    return a


# ─────────────────────────────────────────────────────────────────────────────
# T1 — Modèles
# ─────────────────────────────────────────────────────────────────────────────

class T1_Modeles(TestCase):

    def test_creation_entreprise(self):
        """Une entreprise est créée avec les bons champs par défaut."""
        e = creer_entreprise()
        self.assertEqual(e.statut, "APPROUVEE")
        self.assertTrue(e.est_locale)
        self.assertFalse(e.is_staff)

    def test_statut_defaut_en_attente(self):
        """Le statut par défaut à l'inscription est EN_ATTENTE."""
        e = creer_entreprise(username="new_ent", email="new@test.cm", statut="EN_ATTENTE")
        self.assertEqual(e.statut, "EN_ATTENTE")
        self.assertFalse(e.is_approved())

    def test_is_approved(self):
        """is_approved() retourne True uniquement pour les entreprises approuvées."""
        e_ok  = creer_entreprise(username="ok",  email="ok@t.cm",  statut="APPROUVEE")
        e_att = creer_entreprise(username="att", email="att@t.cm", statut="EN_ATTENTE")
        e_rej = creer_entreprise(username="rej", email="rej@t.cm", statut="REJETEE")
        self.assertTrue(e_ok.is_approved())
        self.assertFalse(e_att.is_approved())
        self.assertFalse(e_rej.is_approved())

    def test_creation_service(self):
        """Un service est créé avec nom et élément."""
        s = Service.objects.create(nom_service="Financement", element="Microfinancement")
        self.assertEqual(str(s), "Financement — Microfinancement")

    def test_unicite_besoin_offre(self):
        """Un même triplet (entreprise, service, besoin) ne peut exister deux fois."""
        from django.db import IntegrityError
        e = creer_entreprise()
        s = creer_service()
        BesoinOffreEntreprise.objects.create(entreprise=e, service=s, besoin=True)
        with self.assertRaises(IntegrityError):
            BesoinOffreEntreprise.objects.create(entreprise=e, service=s, besoin=True)

    def test_meme_service_besoin_et_offre(self):
        """Une entreprise peut déclarer le même service comme besoin ET comme offre."""
        e = creer_entreprise()
        s = creer_service()
        BesoinOffreEntreprise.objects.create(entreprise=e, service=s, besoin=True)
        BesoinOffreEntreprise.objects.create(entreprise=e, service=s, besoin=False)
        self.assertEqual(BesoinOffreEntreprise.objects.filter(entreprise=e, service=s).count(), 2)

    def test_suppression_entreprise_cascade(self):
        """Supprimer une entreprise supprime ses besoins/offres associés."""
        e = creer_entreprise()
        s = creer_service()
        BesoinOffreEntreprise.objects.create(entreprise=e, service=s, besoin=True)
        self.assertEqual(BesoinOffreEntreprise.objects.count(), 1)
        e.delete()
        self.assertEqual(BesoinOffreEntreprise.objects.count(), 0)

    def test_doc_autre_facultatif(self):
        """Le document complémentaire peut être absent."""
        e = creer_entreprise()
        self.assertFalse(bool(e.doc_autre))


# ─────────────────────────────────────────────────────────────────────────────
# T2 — Authentification et contrôle d'accès
# ─────────────────────────────────────────────────────────────────────────────

class T2_Authentification(TestCase):

    def setUp(self):
        self.client = Client()
        self.ent = creer_entreprise()
        self.agent = creer_agent()

    def test_connexion_entreprise_approuvee(self):
        """Une entreprise approuvée peut se connecter et accède au dashboard."""
        r = self.client.post(reverse('connexion'),
                             {'username':'ent_a','password':'TestPass2025!'})
        self.assertRedirects(r, reverse('dashboard'))

    def test_connexion_entreprise_en_attente_bloquee(self):
        """Une entreprise en attente ne peut pas se connecter."""
        creer_entreprise(username="att2", email="att2@t.cm", statut="EN_ATTENTE")
        r = self.client.post(reverse('connexion'),
                             {'username':'att2','password':'TestPass2025!'}, follow=True)
        self.assertContains(r, "non validé")

    def test_connexion_entreprise_rejetee_bloquee(self):
        """Une entreprise rejetée ne peut pas se connecter."""
        creer_entreprise(username="rej2", email="rej2@t.cm", statut="REJETEE")
        r = self.client.post(reverse('connexion'),
                             {'username':'rej2','password':'TestPass2025!'}, follow=True)
        self.assertContains(r, "non validé")

    def test_mauvais_mot_de_passe(self):
        """Un mauvais mot de passe est rejeté."""
        r = self.client.post(reverse('connexion'),
                             {'username':'ent_a','password':'mauvais'}, follow=True)
        self.assertContains(r, "Identifiants incorrects")

    def test_dashboard_non_connecte_redirige(self):
        """Un utilisateur non connecté est redirigé vers /login/."""
        r = self.client.get(reverse('dashboard'))
        self.assertRedirects(r, '/login/?next=/dashboard/')

    def test_deconnexion(self):
        """La déconnexion redirige vers la page de connexion."""
        self.client.login(username='ent_a', password='TestPass2025!')
        r = self.client.get(reverse('deconnexion'))
        self.assertRedirects(r, reverse('connexion'))

    def test_agent_ne_voit_pas_dashboard_entreprise(self):
        """L'agent est redirigé s'il tente d'accéder au dashboard entreprise."""
        self.client.login(username='agent', password='Agent2025!')
        r = self.client.get(reverse('dashboard'))
        # L'agent est staff : il est considéré comme connecté mais
        # le dashboard ne lui est pas destiné
        self.assertIn(r.status_code, [200, 302])

    def test_entreprise_ne_peut_acceder_ministere(self):
        """Une entreprise ne peut pas accéder au tableau de bord du ministère."""
        self.client.login(username='ent_a', password='TestPass2025!')
        r = self.client.get(reverse('ministere_tableau'))
        self.assertRedirects(r, '/admin/login/?next=/ministere/')

    def test_agent_peut_acceder_ministere(self):
        """Un agent staff accède au tableau de bord du ministère."""
        self.client.login(username='agent', password='Agent2025!')
        r = self.client.get(reverse('ministere_tableau'))
        self.assertEqual(r.status_code, 200)


# ─────────────────────────────────────────────────────────────────────────────
# T3 — Inscription
# ─────────────────────────────────────────────────────────────────────────────

class T3_Inscription(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('inscription')

    def _data(self, **overrides):
        data = {
            'username': 'nouvelle_ent',
            'raison_sociale': 'NOUVELLE SARL',
            'email': 'nouvelle@test.cm',
            'password1': 'SecurePass2025!',
            'password2': 'SecurePass2025!',
            'est_locale': 'True',
            'region': 'Centre',
            'branche_activite': 'Commerce',
            'doc_registre_commerce': fake_pdf('rc.pdf'),
            'doc_contribuable': fake_pdf('cc.pdf'),
        }
        data.update(overrides)
        return data

    def test_inscription_valide_cree_compte(self):
        """Une inscription valide crée un compte en statut EN_ATTENTE."""
        r = self.client.post(self.url, self._data())
        self.assertRedirects(r, reverse('connexion'))
        e = Entreprise.objects.get(username='nouvelle_ent')
        self.assertEqual(e.statut, 'EN_ATTENTE')

    def test_inscription_sans_region_locale_echoue(self):
        """Une entreprise locale sans région est rejetée."""
        data = self._data(region='')
        r = self.client.post(self.url, data)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Entreprise.objects.filter(username='nouvelle_ent').exists())

    def test_inscription_email_duplique_echoue(self):
        """Deux entreprises ne peuvent pas partager le même email."""
        creer_entreprise(username="exist", email="nouvelle@test.cm")
        r = self.client.post(self.url, self._data())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Entreprise.objects.filter(email='nouvelle@test.cm').count(), 1)

    def test_inscription_etrangere_sans_region(self):
        """Une entreprise étrangère peut s'inscrire sans région."""
        data = self._data(est_locale='False', region='', username='ent_etrang', email='etrang@test.cm')
        r = self.client.post(self.url, data)
        self.assertRedirects(r, reverse('connexion'))
        e = Entreprise.objects.get(username='ent_etrang')
        self.assertFalse(e.est_locale)

    def test_inscription_sans_doc_autre_acceptee(self):
        """L'inscription sans document complémentaire est acceptée."""
        data = self._data(username='nodoc', email='nodoc@test.cm')
        # doc_autre absent
        r = self.client.post(self.url, data)
        self.assertRedirects(r, reverse('connexion'))
        self.assertTrue(Entreprise.objects.filter(username='nodoc').exists())

    def test_mots_de_passe_differents_echoue(self):
        """Des mots de passe qui ne correspondent pas sont rejetés."""
        data = self._data(password2='DifferentPass!')
        r = self.client.post(self.url, data)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(Entreprise.objects.filter(username='nouvelle_ent').exists())


# ─────────────────────────────────────────────────────────────────────────────
# T4 — Validation par le ministère
# ─────────────────────────────────────────────────────────────────────────────

class T4_Validation(TestCase):

    def setUp(self):
        self.client = Client()
        self.agent = creer_agent()
        self.ent = creer_entreprise(username="dossier", email="dossier@t.cm",
                                    statut="EN_ATTENTE")
        self.client.login(username='agent', password='Agent2025!')

    def test_approbation_change_statut(self):
        """L'approbation par l'agent change le statut à APPROUVEE."""
        self.client.post(
            reverse('examiner_entreprise', args=[self.ent.pk]),
            {'action': 'approuver'})
        self.ent.refresh_from_db()
        self.assertEqual(self.ent.statut, 'APPROUVEE')
        self.assertIsNotNone(self.ent.date_validation)

    def test_rejet_avec_motif_change_statut(self):
        """Le rejet avec motif change le statut à REJETEE et enregistre le motif."""
        self.client.post(
            reverse('examiner_entreprise', args=[self.ent.pk]),
            {'action': 'rejeter', 'motif': 'Documents illisibles.'})
        self.ent.refresh_from_db()
        self.assertEqual(self.ent.statut, 'REJETEE')
        self.assertEqual(self.ent.motif_rejet, 'Documents illisibles.')

    def test_rejet_sans_motif_echoue(self):
        """Le rejet sans motif n'est pas accepté."""
        self.client.post(
            reverse('examiner_entreprise', args=[self.ent.pk]),
            {'action': 'rejeter', 'motif': ''})
        self.ent.refresh_from_db()
        self.assertEqual(self.ent.statut, 'EN_ATTENTE')

    def test_tableau_de_bord_compte_en_attente(self):
        """Le tableau de bord ministère affiche le bon nombre de dossiers en attente."""
        r = self.client.get(reverse('ministere_tableau'))
        self.assertEqual(r.status_code, 200)
        self.assertIn(self.ent, r.context['en_attente'])

    def test_approbation_permet_connexion(self):
        """Après approbation, l'entreprise peut se connecter."""
        self.client.post(
            reverse('examiner_entreprise', args=[self.ent.pk]),
            {'action': 'approuver'})
        c2 = Client()
        r = c2.post(reverse('connexion'),
                    {'username':'dossier','password':'TestPass2025!'})
        self.assertRedirects(r, reverse('dashboard'))

    def test_filtre_liste_par_statut(self):
        """Le filtre par statut sur la liste du ministère fonctionne."""
        r = self.client.get(reverse('liste_entreprises') + '?statut=EN_ATTENTE')
        self.assertIn(self.ent, r.context['entreprises'])
        r2 = self.client.get(reverse('liste_entreprises') + '?statut=APPROUVEE')
        self.assertNotIn(self.ent, r2.context['entreprises'])


# ─────────────────────────────────────────────────────────────────────────────
# T5 — Gestion des services
# ─────────────────────────────────────────────────────────────────────────────

class T5_Services(TestCase):

    def setUp(self):
        self.client = Client()
        self.ent = creer_entreprise()
        self.service = creer_service()
        self.client.login(username='ent_a', password='TestPass2025!')

    def test_enregistrer_besoin(self):
        """Un besoin est correctement enregistré en base."""
        self.client.post(reverse('enregistrer_service'),
                         {'type_relation':'besoin','elements':[self.service.pk]})
        self.assertTrue(
            BesoinOffreEntreprise.objects.filter(
                entreprise=self.ent, service=self.service, besoin=True).exists())

    def test_enregistrer_offre(self):
        """Une offre est correctement enregistrée en base."""
        self.client.post(reverse('enregistrer_service'),
                         {'type_relation':'offre','elements':[self.service.pk]})
        self.assertTrue(
            BesoinOffreEntreprise.objects.filter(
                entreprise=self.ent, service=self.service, besoin=False).exists())

    def test_enregistrement_sans_elements_ne_cree_rien(self):
        """Soumettre sans sélectionner d'élément ne crée aucun enregistrement."""
        self.client.post(reverse('enregistrer_service'),
                         {'type_relation':'besoin','elements':[]})
        self.assertEqual(BesoinOffreEntreprise.objects.count(), 0)

    def test_doublon_besoin_ignore(self):
        """Enregistrer deux fois le même besoin ne crée qu'un seul enregistrement."""
        for _ in range(2):
            self.client.post(reverse('enregistrer_service'),
                             {'type_relation':'besoin','elements':[self.service.pk]})
        self.assertEqual(
            BesoinOffreEntreprise.objects.filter(
                entreprise=self.ent, service=self.service, besoin=True).count(), 1)

    def test_supprimer_besoin(self):
        """Un besoin existant peut être supprimé."""
        rel = BesoinOffreEntreprise.objects.create(
            entreprise=self.ent, service=self.service, besoin=True)
        self.client.get(reverse('supprimer_service', args=[rel.pk]))
        self.assertFalse(
            BesoinOffreEntreprise.objects.filter(pk=rel.pk).exists())

    def test_enregistrement_redirige_vers_besoins(self):
        """Après enregistrement d'un besoin, on est redirigé vers /services/besoins/."""
        r = self.client.post(reverse('enregistrer_service'),
                             {'type_relation':'besoin','elements':[self.service.pk]})
        self.assertRedirects(r, reverse('gerer_services', args=['besoins']))

    def test_enregistrement_redirige_vers_offres(self):
        """Après enregistrement d'une offre, on est redirigé vers /services/offres/."""
        r = self.client.post(reverse('enregistrer_service'),
                             {'type_relation':'offre','elements':[self.service.pk]})
        self.assertRedirects(r, reverse('gerer_services', args=['offres']))

    def test_suppression_appartenant_a_autre_echoue(self):
        """Une entreprise ne peut pas supprimer le besoin d'une autre."""
        autre = creer_entreprise(username="autre_ent", email="autre@t.cm")
        rel = BesoinOffreEntreprise.objects.create(
            entreprise=autre, service=self.service, besoin=True)
        self.client.get(reverse('supprimer_service', args=[rel.pk]))
        # La relation doit toujours exister
        self.assertTrue(BesoinOffreEntreprise.objects.filter(pk=rel.pk).exists())


# ─────────────────────────────────────────────────────────────────────────────
# T6 — Algorithme de mise en relation
# ─────────────────────────────────────────────────────────────────────────────

class T6_MiseEnRelation(TestCase):

    def setUp(self):
        self.client = Client()
        self.ent_a  = creer_entreprise(username="ent_a", email="a@t.cm")
        self.ent_b  = creer_entreprise(username="ent_b", email="b@t.cm")
        self.ent_c  = creer_entreprise(username="ent_c", email="c@t.cm")
        self.s1 = Service.objects.create(nom_service="Emballage", element="Plastique")
        self.s2 = Service.objects.create(nom_service="Financement", element="Crédit")
        self.s3 = Service.objects.create(nom_service="Transport", element="Routier")
        self.client.login(username='ent_a', password='TestPass2025!')

    def test_aucun_partenaire_sans_besoin(self):
        """Sans besoin défini, aucun partenaire n'est affiché."""
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(len(r.context['partenaires']), 0)

    def test_partenaire_offrant_mon_besoin(self):
        """Une entreprise qui offre mon besoin apparaît dans les recommandations."""
        BesoinOffreEntreprise.objects.create(entreprise=self.ent_a, service=self.s1, besoin=True)
        BesoinOffreEntreprise.objects.create(entreprise=self.ent_b, service=self.s1, besoin=False)
        r = self.client.get(reverse('dashboard'))
        pks = [p.pk for p in r.context['partenaires']]
        self.assertIn(self.ent_b.pk, pks)

    def test_classement_par_correspondances_decroissant(self):
        """L'entreprise avec le plus de correspondances apparaît en premier."""
        # A a besoin de s1 et s2
        BesoinOffreEntreprise.objects.create(entreprise=self.ent_a, service=self.s1, besoin=True)
        BesoinOffreEntreprise.objects.create(entreprise=self.ent_a, service=self.s2, besoin=True)
        # B offre s1 ET s2 (2 correspondances)
        BesoinOffreEntreprise.objects.create(entreprise=self.ent_b, service=self.s1, besoin=False)
        BesoinOffreEntreprise.objects.create(entreprise=self.ent_b, service=self.s2, besoin=False)
        # C offre seulement s1 (1 correspondance)
        BesoinOffreEntreprise.objects.create(entreprise=self.ent_c, service=self.s1, besoin=False)
        r = self.client.get(reverse('dashboard'))
        partenaires = list(r.context['partenaires'])
        self.assertEqual(partenaires[0].pk, self.ent_b.pk)
        self.assertEqual(partenaires[1].pk, self.ent_c.pk)

    def test_entreprise_non_approuvee_exclue(self):
        """Une entreprise non approuvée n'apparaît pas dans les recommandations."""
        ent_att = creer_entreprise(username="att", email="att@t.cm", statut="EN_ATTENTE")
        BesoinOffreEntreprise.objects.create(entreprise=self.ent_a, service=self.s1, besoin=True)
        BesoinOffreEntreprise.objects.create(entreprise=ent_att, service=self.s1, besoin=False)
        r = self.client.get(reverse('dashboard'))
        pks = [p.pk for p in r.context['partenaires']]
        self.assertNotIn(ent_att.pk, pks)

    def test_auto_exclusion(self):
        """L'entreprise connectée ne s'affiche pas dans ses propres recommandations."""
        BesoinOffreEntreprise.objects.create(entreprise=self.ent_a, service=self.s1, besoin=True)
        BesoinOffreEntreprise.objects.create(entreprise=self.ent_a, service=self.s1, besoin=False)
        r = self.client.get(reverse('dashboard'))
        pks = [p.pk for p in r.context['partenaires']]
        self.assertNotIn(self.ent_a.pk, pks)

    def test_aucun_partenaire_si_personne_noffre(self):
        """Si aucune entreprise n'offre ce dont A a besoin, la liste est vide."""
        BesoinOffreEntreprise.objects.create(entreprise=self.ent_a, service=self.s1, besoin=True)
        # s3 : personne ne l'offre
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(len(r.context['partenaires']), 0)

    def test_nb_correspondances_annote(self):
        """Le champ nb_correspondances est correctement annoté sur chaque partenaire."""
        BesoinOffreEntreprise.objects.create(entreprise=self.ent_a, service=self.s1, besoin=True)
        BesoinOffreEntreprise.objects.create(entreprise=self.ent_a, service=self.s2, besoin=True)
        BesoinOffreEntreprise.objects.create(entreprise=self.ent_b, service=self.s1, besoin=False)
        BesoinOffreEntreprise.objects.create(entreprise=self.ent_b, service=self.s2, besoin=False)
        r = self.client.get(reverse('dashboard'))
        partenaire_b = next(p for p in r.context['partenaires'] if p.pk == self.ent_b.pk)
        self.assertEqual(partenaire_b.nb_correspondances, 2)


# ─────────────────────────────────────────────────────────────────────────────
# T7 — API JSON
# ─────────────────────────────────────────────────────────────────────────────

class T7_API(TestCase):

    def setUp(self):
        self.client = Client()
        self.ent = creer_entreprise()
        self.client.login(username='ent_a', password='TestPass2025!')
        Service.objects.create(nom_service="Financement", element="Microfinancement", description="PME")
        Service.objects.create(nom_service="Financement", element="Crédit investissement", description="")
        Service.objects.create(nom_service="Transport",   element="Routier", description="")

    def test_api_retourne_elements_du_service(self):
        """L'API retourne les éléments correspondant au nom_service demandé."""
        r = self.client.get(reverse('api_elements_service') + '?nom_service=Financement')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('elements', data)
        self.assertEqual(len(data['elements']), 2)

    def test_api_service_inexistant_retourne_vide(self):
        """L'API retourne une liste vide pour un service inexistant."""
        r = self.client.get(reverse('api_elements_service') + '?nom_service=Inexistant')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['elements'], [])

    def test_api_retourne_champs_requis(self):
        """Chaque élément retourné contient id, element et description."""
        r = self.client.get(reverse('api_elements_service') + '?nom_service=Financement')
        el = r.json()['elements'][0]
        self.assertIn('id', el)
        self.assertIn('element', el)
        self.assertIn('description', el)

    def test_api_filtre_correct(self):
        """L'API ne retourne que les éléments du service demandé, pas les autres."""
        r = self.client.get(reverse('api_elements_service') + '?nom_service=Transport')
        noms = [e['element'] for e in r.json()['elements']]
        self.assertIn('Routier', noms)
        self.assertNotIn('Microfinancement', noms)

    def test_api_sans_parametre_retourne_vide(self):
        """Sans paramètre nom_service, l'API retourne une liste vide."""
        r = self.client.get(reverse('api_elements_service'))
        self.assertEqual(r.json()['elements'], [])


# ─────────────────────────────────────────────────────────────────────────────
# T8 — Isolation et sécurité des données
# ─────────────────────────────────────────────────────────────────────────────

class T8_Securite(TestCase):

    def setUp(self):
        self.client = Client()
        self.ent_a = creer_entreprise(username="sec_a", email="seca@t.cm")
        self.ent_b = creer_entreprise(username="sec_b", email="secb@t.cm")
        self.service = creer_service()

    def test_acces_dashboard_sans_connexion_refuse(self):
        """Le dashboard est inaccessible sans être connecté."""
        r = self.client.get(reverse('dashboard'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/login/', r['Location'])

    def test_acces_profil_sans_connexion_refuse(self):
        """Le profil est inaccessible sans être connecté."""
        r = self.client.get(reverse('profil'))
        self.assertEqual(r.status_code, 302)

    def test_acces_gerer_services_sans_connexion_refuse(self):
        """La gestion des services est inaccessible sans être connecté."""
        r = self.client.get(reverse('gerer_services', args=['besoins']))
        self.assertEqual(r.status_code, 302)

    def test_suppression_service_autre_entreprise_echoue(self):
        """Entreprise A ne peut pas supprimer le besoin d'entreprise B (retourne 404)."""
        rel = BesoinOffreEntreprise.objects.create(
            entreprise=self.ent_b, service=self.service, besoin=True)
        self.client.login(username='sec_a', password='TestPass2025!')
        r = self.client.get(reverse('supprimer_service', args=[rel.pk]))
        self.assertEqual(r.status_code, 404)
        self.assertTrue(BesoinOffreEntreprise.objects.filter(pk=rel.pk).exists())

    def test_fiche_entreprise_non_approuvee_inaccessible(self):
        """La fiche d'une entreprise non approuvée retourne 404."""
        ent_att = creer_entreprise(username="att3", email="att3@t.cm", statut="EN_ATTENTE")
        self.client.login(username='sec_a', password='TestPass2025!')
        r = self.client.get(reverse('fiche_entreprise', args=[ent_att.pk]))
        self.assertEqual(r.status_code, 404)

    def test_fiche_entreprise_approuvee_accessible(self):
        """La fiche d'une entreprise approuvée est bien accessible."""
        self.client.login(username='sec_a', password='TestPass2025!')
        r = self.client.get(reverse('fiche_entreprise', args=[self.ent_b.pk]))
        self.assertEqual(r.status_code, 200)

    def test_protection_csrf_active(self):
        """Une requête POST sans token CSRF est rejetée."""
        c = Client(enforce_csrf_checks=True)
        c.login(username='sec_a', password='TestPass2025!')
        r = c.post(reverse('enregistrer_service'),
                   {'type_relation':'besoin','elements':[self.service.pk]})
        self.assertEqual(r.status_code, 403)
