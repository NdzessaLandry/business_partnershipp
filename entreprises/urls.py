from django.urls import path
from . import views

urlpatterns = [
    path('inscription/', views.inscription, name='inscription'),
    path('login/', views.connexion, name='connexion'),
    path('logout/', views.deconnexion, name='deconnexion'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profil/', views.profil, name='profil'),
    path('services/enregistrer/', views.enregistrer_service, name='enregistrer_service'),
    path('services/supprimer/<int:pk>/', views.supprimer_service, name='supprimer_service'),
    path('services/<str:type_relation>/', views.gerer_services, name='gerer_services'),
    path('entreprise/<int:pk>/', views.fiche_entreprise, name='fiche_entreprise'),
    path('api/elements/', views.api_elements_service, name='api_elements_service'),
]
