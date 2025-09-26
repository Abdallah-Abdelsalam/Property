from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.urls import reverse
from django.dispatch import receiver
import urllib.parse

from django.http import HttpRequest
from django.conf import settings


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('client', 'Client'),
        ('admin', 'Admin/Manager'),
        ('agent', 'Sales Agent'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    phone = models.CharField(max_length=15, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

# Signal to create user profile when a user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        UserProfile.objects.create(user=instance)

class PropertyType(models.Model):
    """Model for dynamic property types that can be added by admin"""
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_name']
    
    def __str__(self):
        return self.display_name

class City(models.Model):
    """Model for dynamic cities that can be added by admin"""
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Cities"
    
    def __str__(self):
        return self.name

class State(models.Model):
    """Model for dynamic states that can be added by admin"""
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
class Address(models.Model):
    """Model for dynamic addresses that can be added by admin"""
    name = models.CharField(max_length=255, unique=True)
    city = models.ForeignKey('City', on_delete=models.PROTECT)
    state = models.ForeignKey('State', on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Addresses"
    
    def __str__(self):
        return f"{self.name}, {self.city.name}, {self.state.name}"

class Property(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    bedrooms = models.IntegerField()
    bathrooms = models.IntegerField()
    area = models.DecimalField(max_digits=10, decimal_places=2, help_text="Area in square meters")
    address = models.ForeignKey('Address', on_delete=models.PROTECT)
    property_type = models.ForeignKey('PropertyType', on_delete=models.PROTECT)
    city = models.ForeignKey('City', on_delete=models.PROTECT)
    state = models.ForeignKey('State', on_delete=models.PROTECT)
    owner_phone = models.CharField(max_length=15, blank=True, verbose_name="Owner's Phone Number")
    main_image = models.ImageField(upload_to='property_images/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    agent = models.ForeignKey(User, on_delete=models.CASCADE)
    is_published = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('property_detail', kwargs={'pk': self.pk})
    
    def whatsapp_share_url(self, request=None):
        # Get the current domain
        if request:
            domain = request.get_host()
            scheme = 'https' if request.is_secure() else 'http'
        else:
            domain = getattr(settings, 'DEFAULT_DOMAIN', '127.0.0.1:8000')
            scheme = getattr(settings, 'DEFAULT_SCHEME', 'http')
        
        # Use the public encrypted URL for sharing
        from .utils import url_encryptor
        encrypted_id = url_encryptor.encrypt_id(self.pk)
        
        # Create the public shareable URL
        property_url = f"{scheme}://{domain}/view/{encrypted_id}/"
        
        # Create a URL-encoded message for WhatsApp sharing
        message = f"🏠 {self.title}\n\n{self.description[:100]}...\n\n{property_url}"
        encoded_message = urllib.parse.quote(message)
        return f"https://wa.me/?text={encoded_message}"

    
    def can_view_owner_phone(self, user):
        """Check if the user can view the owner's phone number"""
        return user.is_authenticated and user == self.agent
    

class PropertyImage(models.Model):
    property = models.ForeignKey(Property, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='property_images/')
    
    def __str__(self):
        return f"Image for {self.property.title}"