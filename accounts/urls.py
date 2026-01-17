from django.urls import path
from django.contrib.auth import views as auth_views
from .views import StyledLoginView, register, logout_view, StyledPasswordResetView, StyledPasswordResetConfirmView

app_name = "accounts"

urlpatterns = [
    path("login/", StyledLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
    path("register/", register, name="register"),
    path("password-reset/", StyledPasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done"),
    path("reset/<uidb64>/<token>/",
        StyledPasswordResetConfirmView.as_view(),
        name="password_reset_confirm"),
    path("reset/done/",
        auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"),
        name="password_reset_complete"),
]
