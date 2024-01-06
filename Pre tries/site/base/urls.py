from django.urls import path
from . import views

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('findprofile/<str:pk>', views.FindProfile.as_view(), name='findprofile'),
]