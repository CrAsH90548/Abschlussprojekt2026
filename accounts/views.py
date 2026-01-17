from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import LoginForm, RegisterForm

class StyledLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, "Willkommen zurück!")
        return super().form_valid(form)

def register(request):
    if request.user.is_authenticated:
        return redirect("frontend")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account erstellt. Viel Spaß!")
            return redirect("frontend")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})

def logout_view(request):
    logout(request)
    messages.info(request, "Du wurdest abgemeldet.")
    return redirect("accounts:login")

class StyledPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.txt"
    success_url = reverse_lazy("accounts:password_reset_done")

class StyledPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")
