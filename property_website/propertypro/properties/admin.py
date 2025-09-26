from django.contrib import admin
from .models import Property, PropertyImage, UserProfile, PropertyType, City, State,Address

# Create an inline for UserProfile to show it in the User admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    fk_name = 'user'

# Custom User Admin to include UserProfile inline
class CustomUserAdmin(admin.ModelAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'get_role', 'first_name', 'last_name', 'is_active', 'is_staff')
    list_filter = ('userprofile__role', 'is_active', 'is_staff')
    list_editable = ('is_active', 'is_staff')
    
    def get_role(self, obj):
        try:
            return obj.userprofile.get_role_display()
        except UserProfile.DoesNotExist:
            return "No Profile"
    get_role.short_description = 'Role'
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)

# Unregister the default User admin and register with custom admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_username', 'role', 'phone', 'is_active_user')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')
    list_editable = ('role',)
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'
    get_username.admin_order_field = 'user__username'
    
    def is_active_user(self, obj):
        return obj.user.is_active
    is_active_user.boolean = True
    is_active_user.short_description = 'Active User'

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1

@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'display_name']
    list_editable = ['is_active']

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    list_editable = ['is_active']

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    list_editable = ['is_active']

@admin.register(Address)
class Addressadmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    list_editable = ['is_active']

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['title', 'property_type', 'city', 'state', 'price', 'is_published', 'agent']
    list_filter = ['property_type', 'city', 'state', 'is_published']
    search_fields = ['title', 'address', 'city__name', 'state__name']
    list_editable = ['is_published']