# Requirement

- Redis Server
- PostgreSQL Server
- Stripe

# Feature

- Real-time Chatroom
- Shopping Cart System
- Product System
- Product Management System
- Product Analysis System

# Setting

./e_commerce_server/setting.py

```python
SECRET_KEY = 'django-insecure-Your Secret Key'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql', 
        'NAME': 'e-commerce-server',
        'USER': 'postgres',
        'PASSWORD': 'Your Database Password',
        'HOST': 'Your Database Host Name (192.168.0.10)',
        'PORT': '6432',
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://Your Redis server ip/8",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

CHANNEL_LAYERS = {
     "default": {
         "BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
         "CONFIG": {
             "hosts": [os.environ.get('REDIS_URL', 'redis://Your Redis server ip/1')],
         },
     },
 }
 
STRIPE_PUBLIC_KEY = 'pk_test_Your Stripe Public Key'
STRIPE_SECRET_KEY = 'sk_test_Your Stripe Secret Key'


JWT_ENV_SETTING = {'ACCESS_TOKEN_LIFETIME': timedelta(minutes=120),
                   'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
                   'EDIT_TOKEN_LIFETIME': timedelta(minutes=15),
                   'algorithm': "Your Target Algorithm (Default HS512)",
                   'secret_key': 'Your Secret Key',
                   "issuer": "ECommerceTech"
                   }
GOOGLE_CLIENT_ID = 'Your Google Client ID.apps.googleusercontent.com'
```
## Available Scripts

##### `python manage.py runserver` for windows user
##### `python3 manage.py runserver` for mac and linux user

## Frontend Server

https://github.com/petersing/E-Commerce-Front-End-

## Declare

This server is still under development, not yet in production, there may be many bugs, welcome to report