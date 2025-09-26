from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User 
from django.contrib import messages
from .models import Property, UserProfile
from django.http import Http404
import urllib.parse

from .models import PropertyImage
from .forms import PropertyForm, PropertyImageForm

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Property, PropertyType, City, State, Address

# Import the URL encryptor
from .utils import url_encryptor

@login_required
def property_list(request):
    # Only allow agents and admins to view properties
    if request.user.userprofile.role not in ['agent', 'admin'] and not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية لعرض العقارات.')
        return redirect('agent_dashboard')
    
    # If user is agent, show only their assigned properties
    if request.user.userprofile.role == 'agent':
        properties = Property.objects.filter(agent=request.user, is_published=True)
    else:  # admin or superuser can see all properties
        properties = Property.objects.filter(is_published=True)
    
    # Get filter options for dropdowns
    property_types = PropertyType.objects.filter(is_active=True)
    cities = City.objects.filter(is_active=True)
    states = State.objects.filter(is_active=True)
    addresses = Address.objects.filter(is_active=True)
    
    # Handle search and filters
    search_query = request.GET.get('search')
    address_id = request.GET.get('address')
    city_id = request.GET.get('city')
    state_id = request.GET.get('state')
    property_type_id = request.GET.get('property_type')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    # Apply filters
    if search_query:
        properties = properties.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if address_id:
        properties = properties.filter(address_id=address_id)
    
    if city_id:
        properties = properties.filter(city_id=city_id)
    
    if state_id:
        properties = properties.filter(state_id=state_id)
    
    if property_type_id:
        properties = properties.filter(property_type_id=property_type_id)
    
    # Apply price filters
    if min_price:
        properties = properties.filter(price__gte=min_price)
    
    if max_price:
        properties = properties.filter(price__lte=max_price)
    
    context = {
        'properties': properties,
        'property_types': property_types,
        'cities': cities,
        'states': states,
        'addresses': addresses,
        'user_role': request.user.userprofile.role,
    }
    
    return render(request, 'properties/property_list.html', context)

def property_detail_public(request, encrypted_id):
    """
    Public property detail - accessible without login via encrypted URL
    """
    # Decrypt the property ID from the URL
    property_id = url_encryptor.decrypt_id(encrypted_id)
    
    print(f"Encrypted ID received: {encrypted_id}")  # Debug
    print(f"Decrypted property ID: {property_id}")   # Debug
    
    if not property_id:
        print("Property ID is None or invalid")  # Debug
        raise Http404("Property not found or invalid link")
    
    try:
        property_obj = Property.objects.get(pk=property_id, is_published=True)
        print(f"Property found: {property_obj.title}")  # Debug
    except Property.DoesNotExist:
        print("Property not found or not published")  # Debug
        raise Http404("Property not found or invalid link")
    
    # For public access, restrict some information
    can_view_owner_phone = False  # Public users can't see phone numbers
    is_public_access = True
    
    # Generate public WhatsApp share URL
    whatsapp_url = generate_public_whatsapp_url(property_obj, request)
    
    return render(request, 'properties/property_detail_public.html', {
        'property': property_obj,
        'whatsapp_url': whatsapp_url,
        'can_view_owner_phone': can_view_owner_phone,
        'is_public_access': is_public_access,
        'shareable_link': request.build_absolute_uri(request.path)
    })

@login_required
def property_detail(request, pk):
    """
    Private property detail - for logged-in users
    """
    # Check if user can view this property
    if request.user.userprofile.role == 'agent':
        # Agents can only view their own properties
        property_obj = get_object_or_404(Property, pk=pk, agent=request.user, is_published=True)
    else:  # admin or superuser can view any property
        property_obj = get_object_or_404(Property, pk=pk, is_published=True)
    
    # Check if user can view owner phone
    can_view_owner_phone = property_obj.can_view_owner_phone(request.user)
    is_public_access = False
    
    # Generate shareable public link for logged-in users to share
    encrypted_id = url_encryptor.encrypt_id(pk)
    shareable_link = request.build_absolute_uri(f'/view/{encrypted_id}/')
    
    return render(request, 'properties/property_detail.html', {
        'property': property_obj,
        'whatsapp_url': property_obj.whatsapp_share_url(request),
        'can_view_owner_phone': can_view_owner_phone,
        'is_public_access': is_public_access,
        'shareable_link': shareable_link
    })

@login_required
def my_properties(request):
    """View for agents to see their own properties"""
    # Ensure only agents can access this view
    if request.user.userprofile.role != 'agent' and not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة.')
        return redirect('agent_dashboard')
    
    properties = Property.objects.filter(agent=request.user, is_published=True)
    
    # Add shareable links for each property
    properties_with_links = []
    for prop in properties:
        encrypted_id = url_encryptor.encrypt_id(prop.pk)
        shareable_link = request.build_absolute_uri(f'/view/{encrypted_id}/')
        properties_with_links.append({
            'property': prop,
            'shareable_link': shareable_link
        })
    
    return render(request, 'properties/my_properties.html', {
        'properties_with_links': properties_with_links,
        'total_properties': properties.count()
    })

def generate_public_whatsapp_url(property_obj, request):
    """Generate WhatsApp share URL with public encrypted link"""
    encrypted_id = url_encryptor.encrypt_id(property_obj.pk)
    public_url = request.build_absolute_uri(f'/view/{encrypted_id}/')
    
    message = f"🏠 {property_obj.title}\n\n{property_obj.description[:100]}...\n\n{public_url}"
    encoded_message = urllib.parse.quote(message)
    return f"https://wa.me/?text={encoded_message}"

# ===== AUTHENTICATION VIEWS =====
def login_view(request):
    if request.user.is_authenticated:
        # Redirect already logged-in users to appropriate dashboard
        try:
            profile = UserProfile.objects.get(user=request.user)
            if profile.role == 'client':
                return redirect('client_dashboard')
            else:
                return redirect('agent_dashboard')
        except UserProfile.DoesNotExist:
            # Create a default profile if it doesn't exist
            profile = UserProfile.objects.create(user=request.user, role='client')
            return redirect('client_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Redirect based on user role
            try:
                profile = UserProfile.objects.get(user=user)
                if profile.role == 'client':
                    return redirect('client_dashboard')
                else:
                    return redirect('agent_dashboard')
            except UserProfile.DoesNotExist:
                # Create a default profile if it doesn't exist
                profile = UserProfile.objects.create(user=user, role='client')
                return redirect('client_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'properties/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def client_dashboard(request):
    # Ensure only clients can access this view
    if request.user.userprofile.role != 'client':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة.')
        return redirect('agent_dashboard')
    
    # Get all sales agents for client to contact
    agents = User.objects.filter(userprofile__role='agent')
    return render(request, 'properties/client_dashboard.html', {'agents': agents})

@login_required
def agent_dashboard(request):
    """Dashboard for agents to view their properties"""
    # Ensure only agents and admins can access this view
    if request.user.userprofile.role not in ['agent', 'admin'] and not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة.')
        return redirect('client_dashboard')
    
    # Agents see only their properties, admins see all
    if request.user.userprofile.role == 'agent':
        properties = Property.objects.filter(agent=request.user)
    else:  # admin or superuser
        properties = Property.objects.all()
    
    # Add shareable links for each property
    properties_with_links = []
    for prop in properties:
        encrypted_id = url_encryptor.encrypt_id(prop.pk)
        shareable_link = request.build_absolute_uri(f'/view/{encrypted_id}/')
        properties_with_links.append({
            'property': prop,
            'shareable_link': shareable_link
        })
    
    # Pass cities and states for admin address form
    cities = City.objects.filter(is_active=True)
    states = State.objects.filter(is_active=True)
    agents = User.objects.filter(userprofile__role='agent')
    
    return render(request, 'properties/agent_dashboard.html', {
        'properties_with_links': properties_with_links,
        'total_properties': properties.count(),
        'cities': cities,
        'states': states,
        'user_role': request.user.userprofile.role,
        'agents': agents 
    })

@login_required
def add_property(request):
    """View for agents to add new properties"""
    # Ensure only agents and admins can add properties
    if request.user.userprofile.role not in ['agent', 'admin'] and not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية لإضافة عقارات.')
        return redirect('client_dashboard')
    
    # Get all agents for admin assignment
    agents = User.objects.filter(userprofile__role='agent')
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            property_obj = form.save(commit=False)
            
            # Set agent based on user role
            if request.user.userprofile.role == 'agent':
                property_obj.agent = request.user
            else:  # admin assigning to an agent
                if request.POST.get('agent'):
                    try:
                        agent_id = request.POST.get('agent')
                        assigned_agent = User.objects.get(id=agent_id)
                        property_obj.agent = assigned_agent
                    except (User.DoesNotExist, ValueError):
                        property_obj.agent = request.user
                else:
                    property_obj.agent = request.user
            
            property_obj.save()
            messages.success(request, 'تم إضافة العقار بنجاح!')
            return redirect('agent_dashboard')
    else:
        form = PropertyForm()
    
    return render(request, 'properties/add_property.html', {
        'form': form,
        'agents': agents,
        'user_role': request.user.userprofile.role
    })

@login_required
def edit_property(request, pk):
    """View for agents to edit their properties"""
    # Check permissions
    if request.user.userprofile.role == 'agent':
        property_obj = get_object_or_404(Property, pk=pk, agent=request.user)
    else:  # admin or superuser can edit any property
        property_obj = get_object_or_404(Property, pk=pk)
    
    # Get all agents for admin assignment
    agents = User.objects.filter(userprofile__role='agent')
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=property_obj)
        if form.is_valid():
            # If admin is assigning to a different agent
            if (request.user.userprofile.role == 'admin' or request.user.is_superuser) and request.POST.get('agent'):
                try:
                    agent_id = request.POST.get('agent')
                    assigned_agent = User.objects.get(id=agent_id)
                    property_obj.agent = assigned_agent
                except (User.DoesNotExist, ValueError):
                    pass
            
            form.save()
            messages.success(request, 'تم تحديث العقار بنجاح!')
            return redirect('agent_dashboard')
    else:
        form = PropertyForm(instance=property_obj)
    
    return render(request, 'properties/edit_property.html', {
        'form': form, 
        'property': property_obj,
        'agents': agents,
        'user_role': request.user.userprofile.role
    })

@login_required
def delete_property(request, pk):
    """View for agents to delete their properties"""
    # Check permissions
    if request.user.userprofile.role == 'agent':
        property_obj = get_object_or_404(Property, pk=pk, agent=request.user)
    else:  # admin or superuser can delete any property
        property_obj = get_object_or_404(Property, pk=pk)
    
    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, 'تم حذف العقار بنجاح!')
        return redirect('agent_dashboard')
    
    return render(request, 'properties/delete_property.html', {'property': property_obj})

@login_required
def add_property_images(request, pk):
    """View for agents to add images to their properties"""
    # Check permissions
    if request.user.userprofile.role == 'agent':
        property_obj = get_object_or_404(Property, pk=pk, agent=request.user)
    else:  # admin or superuser can add images to any property
        property_obj = get_object_or_404(Property, pk=pk)
    
    if request.method == 'POST':
        form = PropertyImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.property = property_obj
            image.save()
            messages.success(request, 'تم إضافة الصورة بنجاح!')
            return redirect('add_property_images', pk=property_obj.pk)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه.')
    else:
        form = PropertyImageForm()
    
    images = property_obj.images.all()
    return render(request, 'properties/add_property_images.html', {
        'form': form, 
        'property': property_obj,
        'images': images
    })


@login_required
def add_city(request):
    if request.user.userprofile.role != 'admin' and not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للقيام بهذا الإجراء')
        return redirect('agent_dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            City.objects.create(name=name)
            messages.success(request, f'تم إضافة المدينة "{name}" بنجاح')
        return redirect('agent_dashboard')
    
    return redirect('agent_dashboard')

@login_required
def add_state(request):
    if request.user.userprofile.role != 'admin' and not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للقيام بهذا الإجراء')
        return redirect('agent_dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            State.objects.create(name=name)
            messages.success(request, f'تم إضافة المنطقة "{name}" بنجاح')
        return redirect('agent_dashboard')
    
    return redirect('agent_dashboard')

@login_required
def add_property_type(request):
    if request.user.userprofile.role != 'admin' and not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للقيام بهذا الإجراء')
        return redirect('agent_dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        display_name = request.POST.get('display_name')
        if name and display_name:
            PropertyType.objects.create(name=name, display_name=display_name)
            messages.success(request, f'تم إضافة نوع العقار "{display_name}" بنجاح')
        return redirect('agent_dashboard')
    
    return redirect('agent_dashboard')

@login_required
def add_address(request):
    if request.user.userprofile.role != 'admin' and not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للقيام بهذا الإجراء')
        return redirect('agent_dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        city_id = request.POST.get('city')
        state_id = request.POST.get('state')
        
        if name and city_id and state_id:
            try:
                city = City.objects.get(id=city_id)
                state = State.objects.get(id=state_id)
                Address.objects.create(name=name, city=city, state=state)
                messages.success(request, f'تم إضافة العنوان "{name}" بنجاح')
            except (City.DoesNotExist, State.DoesNotExist):
                messages.error(request, 'المدينة أو المنطقة غير صحيحة')
        else:
            messages.error(request, 'يرجى ملء جميع الحقول')
        
        return redirect('agent_dashboard')
    
    return redirect('agent_dashboard')



@login_required
def create_agent(request):
    """View for admins to create new sales agents"""
    # Ensure only admins can create agents
    if request.user.userprofile.role != 'admin' and not request.user.is_superuser:
        messages.error(request, 'ليس لديك صلاحية للقيام بهذا الإجراء')
        return redirect('agent_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone = request.POST.get('phone', '')
        
        # Validate passwords match
        if password != confirm_password:
            messages.error(request, 'كلمات المرور غير متطابقة')
            return redirect('agent_dashboard')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'اسم المستخدم موجود مسبقاً')
            return redirect('agent_dashboard')
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'البريد الإلكتروني موجود مسبقاً')
            return redirect('agent_dashboard')
        
        # Create the user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Set the user role to agent
            user_profile = user.userprofile
            user_profile.role = 'agent'
            if phone:
                user_profile.phone = phone
            user_profile.save()
            
            messages.success(request, f'تم إنشاء حساب الوسيط "{username}" بنجاح')
            
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء إنشاء الحساب: {str(e)}')
        
        return redirect('agent_dashboard')
    
    return redirect('agent_dashboard')