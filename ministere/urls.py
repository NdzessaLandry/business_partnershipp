from django.urls import path
from . import views

urlpatterns = [
    path('', views.tableau_de_bord, name='ministere_tableau'),
    path('entreprise/<int:pk>/', views.examiner_entreprise, name='examiner_entreprise'),
    path('entreprises/', views.liste_entreprises, name='liste_entreprises'),
]
