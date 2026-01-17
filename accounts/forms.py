from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="E-Mail",
        widget=forms.TextInput(attrs={"placeholder": "z. B. max@firma.de"}),
    )
    password = forms.CharField(
        label="Passwort",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
    )

class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(label="Passwort", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Passwort (Wiederholung)", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("username", "email")
        labels = {"username": "Benutzername","email": "E-Mail"}
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "z. B. max"}),
            "email": forms.EmailInput(attrs={"placeholder": "z. B. max@firma.de"}),
        }

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwörter stimmen nicht überein.")
        return cleaned

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Diese E-Mail wird bereits verwendet.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
