# setup_django.py
# 285IQ Django Backend Setup Script
# This creates the complete Django project structure

import os
import subprocess
import sys

def check_django_installed():
    """Check if Django is installed, install if not"""
    try:
        import django
        print(f"✅ Django {django.get_version()} is already installed")
        return True
    except ImportError:
        print("📦 Django not found. Installing Django...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "django"])
            print("✅ Django installed successfully!")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install Django. Please install manually:")
            print("   pip install django")
            return False

def create_django_project():
    """Create the Django project structure"""
    print("🏗️ Creating Django project structure...")
    
    # Change to the django_backend directory
    backend_dir = "django_backend"
    
    if not os.path.exists(backend_dir):
        os.makedirs(backend_dir)
    
    os.chdir(backend_dir)
    
    # Create Django project
    try:
        subprocess.check_call(["django-admin", "startproject", "studymate285", "."])
        print("✅ Django project 'studymate285' created!")
    except subprocess.CalledProcessError:
        print("❌ Failed to create Django project")
        return False
    
    # Create Django apps
    apps = ["users", "learning", "gamification", "content"]
    
    for app in apps:
        try:
            subprocess.check_call([sys.executable, "manage.py", "startapp", app])
            print(f"✅ App '{app}' created!")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to create app '{app}'")
            return False
    
    return True

def create_requirements_file():
    """Create requirements.txt for the project"""
    requirements = """Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.1
psycopg2-binary==2.9.9
python-decouple==3.8
Pillow==10.1.0
django-extensions==3.2.3
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements)
    
    print("✅ requirements.txt created!")

def create_env_template():
    """Create .env template file"""
    env_template = """# 285IQ Environment Variables
# Copy this to .env and fill in your values

SECRET_KEY=your-super-secret-key-here-change-this
DEBUG=True
DB_NAME=285iq_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Add these later when you get API keys
# OPENAI_API_KEY=your-openai-key
# STRIPE_SECRET_KEY=your-stripe-key
"""
    
    with open(".env.example", "w") as f:
        f.write(env_template)
    
    print("✅ .env.example created!")

def create_basic_settings():
    """Create enhanced settings.py"""
    settings_content = '''"""
Django settings for studymate285 project.
"""

from pathlib import Path
from decouple import config
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '285iq.com', 'www.285iq.com']

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
]

LOCAL_APPS = [
    'users',
    'learning',
    'gamification', 
    'content',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'studymate285.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'studymate285.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'Europe/London'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# CORS settings for frontend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React development server
    "https://285iq.com",
    "https://www.285iq.com",
]

CORS_ALLOW_CREDENTIALS = True

# Custom user model (we'll create this)
AUTH_USER_MODEL = 'users.Student'
'''

    # Write the settings file
    settings_path = os.path.join("studymate285", "settings.py")
    with open(settings_path, "w") as f:
        f.write(settings_content)
    
    print("✅ Enhanced settings.py created!")

def create_main_urls():
    """Create main URL configuration"""
    urls_content = '''"""
285IQ URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/learning/', include('learning.urls')),
    path('api/gamification/', include('gamification.urls')),
    path('api/content/', include('content.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
'''

    urls_path = os.path.join("studymate285", "urls.py")
    with open(urls_path, "w") as f:
        f.write(urls_content)
    
    print("✅ Main URLs configuration created!")

def create_app_urls():
    """Create URL files for each app"""
    apps = ["users", "learning", "gamification", "content"]
    
    for app in apps:
        urls_content = f'''"""
URLs for {app} app
"""
from django.urls import path
from . import views

app_name = '{app}'

urlpatterns = [
    # URLs will be added here as we build features
    path('', views.placeholder_view, name='placeholder'),
]
'''
        
        urls_path = os.path.join(app, "urls.py")
        with open(urls_path, "w") as f:
            f.write(urls_content)
        
        print(f"✅ {app}/urls.py created!")

def create_placeholder_views():
    """Create placeholder views for each app"""
    apps = ["users", "learning", "gamification", "content"]
    
    for app in apps:
        views_content = f'''"""
Views for {app} app
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def placeholder_view(request):
    """Placeholder view - will be replaced with real functionality"""
    return Response({{
        'message': f'{app.title()} app is ready!',
        'status': 'placeholder'
    }})
'''
        
        views_path = os.path.join(app, "views.py")
        with open(views_path, "w") as f:
            f.write(views_content)
        
        print(f"✅ {app}/views.py created!")

def setup_initial_migration():
    """Set up initial database migration"""
    print("🗄️ Setting up initial database...")
    
    try:
        # Run initial migration
        subprocess.check_call([sys.executable, "manage.py", "migrate"])
        print("✅ Initial database migration completed!")
        
        # Create superuser script
        create_superuser_script = '''
# Create superuser for admin access
from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@285iq.com',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    print("Superuser 'admin' created! Password: admin123")
else:
    print("Superuser already exists")
'''
        
        with open("create_superuser.py", "w") as f:
            f.write(create_superuser_script)
        
        print("✅ Superuser creation script ready!")
        
    except subprocess.CalledProcessError:
        print("⚠️ Migration failed - this is normal if we haven't created models yet")

def create_project_readme():
    """Create README with setup instructions"""
    readme_content = '''# 285IQ Learning Platform

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Run Migrations
```bash
python manage.py migrate
```

### 4. Create Superuser
```bash
python manage.py shell < create_superuser.py
```

### 5. Run Development Server
```bash
python manage.py runserver
```

Visit: http://localhost:8000/admin (admin/admin123)

## 📁 Project Structure

```
django_backend/
├── studymate285/          # Main project settings
├── users/                 # User management & authentication
├── learning/              # Learning sessions & progress
├── gamification/          # XP, achievements, leaderboards  
├── content/               # Topics, questions, videos
├── templates/             # HTML templates
├── static/                # CSS, JS, images
└── media/                 # User uploads
```

## 🎯 Next Steps

1. Create user models (Student, Teacher, etc.)
2. Build content models (Topic, Question, etc.) 
3. Add authentication APIs
4. Create learning session tracking
5. Implement XP and gamification
6. Connect to frontend

## 🔧 Development Commands

```bash
# Run server
python manage.py runserver

# Create new app
python manage.py startapp appname

# Make migrations
python manage.py makemigrations

# Apply migrations  
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Shell
python manage.py shell
```
'''
    
    with open("README.md", "w") as f:
        f.write(readme_content)
    
    print("✅ README.md created!")

def main():
    """Main setup function"""
    print("🎓 285IQ Django Backend Setup")
    print("=" * 40)
    
    # Check Django installation
    if not check_django_installed():
        return
    
    # Create project structure
    if not create_django_project():
        return
    
    # Create additional files
    create_requirements_file()
    create_env_template()
    create_basic_settings()
    create_main_urls()
    create_app_urls()
    create_placeholder_views()
    setup_initial_migration()
    create_project_readme()
    
    print("\n🎉 Django backend setup complete!")
    print("\n📋 Next steps:")
    print("1. cd django_backend")
    print("2. pip install -r requirements.txt")
    print("3. python manage.py runserver")
    print("4. Visit http://localhost:8000/admin")
    print("\n✨ Your Django backend is ready to build amazing features!")

if __name__ == "__main__":
    main()