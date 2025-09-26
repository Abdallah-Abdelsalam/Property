from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('', login_required(views.property_list), name='property_list'),
    
    # Public shareable URL (no login required) - encrypted
    path('view/<str:encrypted_id>/', views.property_detail_public, name='property_detail_public'),
    
    # Private URL for logged-in users (original pattern)
    path('property/<int:pk>/', login_required(views.property_detail), name='property_detail'),
    
    path('my-properties/', login_required(views.my_properties), name='my_properties'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='properties/login.html'), name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('client-dashboard/', login_required(views.client_dashboard), name='client_dashboard'),
    path('agent/dashboard/', login_required(views.agent_dashboard), name='agent_dashboard'),
    path('agent/property/add/', login_required(views.add_property), name='add_property'),
    path('agent/property/<int:pk>/edit/', login_required(views.edit_property), name='edit_property'),
    path('agent/property/<int:pk>/delete/', login_required(views.delete_property), name='delete_property'),
    path('agent/property/<int:pk>/images/', login_required(views.add_property_images), name='add_property_images'),

    path('add-city/', login_required(views.add_city), name='add_city'),
    path('add-state/', login_required(views.add_state), name='add_state'),
    path('add-property-type/', login_required(views.add_property_type), name='add_property_type'),
    path('add-address/', login_required(views.add_address), name='add_address'),
    path('create-agent/', views.create_agent, name='create_agent'),
]