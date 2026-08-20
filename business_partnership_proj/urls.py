from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from entreprises.views import PasswordResetViewCorrigee

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda r: redirect('connexion'), name='home'),
    path('', include('entreprises.urls')),
    path('ministere/', include('ministere.urls')),
    path('mot-de-passe/reinitialiser/',
         PasswordResetViewCorrigee.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt',
             success_url='/mot-de-passe/reinitialiser/envoye/',
         ),
         name='password_reset'),

    path('mot-de-passe/reinitialiser/envoye/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html',
         ),
         name='password_reset_done'),

    path('mot-de-passe/reinitialiser/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url='/mot-de-passe/reinitialiser/termine/',
         ),
         name='password_reset_confirm'),

    path('mot-de-passe/reinitialiser/termine/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html',
         ),
         name='password_reset_complete'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
