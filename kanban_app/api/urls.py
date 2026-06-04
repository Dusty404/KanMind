from django.urls import path


from .views import EmailCheckView

urlpatterns = [
    path("email-check/", EmailCheckView.as_view())
]
