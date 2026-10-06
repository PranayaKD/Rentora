# Rentora - Automotive Fleet Rental & Booking Engine

[![Django](https://img.shields.io/badge/Django-5.2+-092e20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Stripe](https://img.shields.io/badge/Payments-Stripe-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://stripe.com/)
[![Razorpay](https://img.shields.io/badge/Payments-Razorpay-0c2340?style=for-the-badge&logo=razorpay&logoColor=white)](https://razorpay.com/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Sentry](https://img.shields.io/badge/Monitoring-Sentry-362D59?style=for-the-badge&logo=sentry&logoColor=white)](https://sentry.io/)
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com/)

🔗 **Live Demo**: [https://rentora.onrender.com](https://rentora.onrender.com) | 📂 **GitHub**: [https://github.com/PranayaKD/Rentora](https://github.com/PranayaKD/Rentora)

## 1. Project Overview
Rentora is a full-stack automotive rental platform engineered for regional self-drive and chauffeur fleet operations. Built with Django and PostgreSQL, the system solves concurrency challenges in equipment reservation by enforcing atomic double-booking prevention, dynamic pricing schedules with weekend surcharge calculations, automated tax computation (GST), and multi-provider transactional payment workflows (Stripe and Razorpay).

## 2. Tech Stack
- Python 3.13
- Django 5.2.4
- PostgreSQL (via psycopg2-binary and dj-database-url)
- Stripe Python SDK
- Razorpay Python SDK
- Django-Allauth (Google OAuth 2.0)
- Twilio SDK (Phone OTP authentication)
- Django-Storages & Boto3 (Supabase S3-compatible cloud object storage)
- Sentry SDK (Application monitoring and error tracking)
- ReportLab & xhtml2pdf (Dynamic PDF invoice and receipt rendering)
- WhiteNoise (Compressed static asset serving)
- Tailwind CSS & Crispy Tailwind (UI templating and forms)

## 3. Architecture
The project follows Django's modular app structure, separating domain models, view controllers, services, and administrative interfaces:

```
Rentora/
├── manage.py                   # Django management entry point
├── Procfile                    # Deployment process configuration
├── requirements.txt            # Production dependencies
├── .env.example                # Environment variables template
├── rentora_project/            # Project configuration root
│   ├── settings.py             # Settings, storage, security & database configuration
│   ├── urls.py                 # Root routing table and media handling
│   ├── wsgi.py                 # WSGI application entry point
│   └── asgi.py                 # ASGI application entry point
├── core/                       # Main business domain & booking engine
│   ├── models.py               # Car, Booking, Review, Wishlist, PromoCode, Notification
│   ├── views.py                # Public catalog, multi-step booking, webhooks, AJAX APIs
│   ├── services.py             # BookingService payment orchestration (Stripe/Razorpay)
│   ├── utils_pdf.py            # PDF invoice generation pipeline
│   ├── forms.py                # Booking location, dates, review, and contact forms
│   ├── urls.py                 # Core routing endpoints
│   └── constants.py            # Financial and taxation constants (GST, referral amounts)
├── accounts/                   # Identity and profile management
│   ├── models.py               # UserProfile with KYC fields and wallet balances
│   ├── views.py                # Authentication, OTP AJAX handlers, dashboard views
│   ├── services.py             # Twilio SMS/OTP verification service
│   ├── middleware.py           # Profile prefetching middleware
│   └── urls.py                 # Auth and dashboard routes
├── admin_panel/                # Custom operational dashboard
│   ├── views.py                # Fleet CRUD, booking state transitions, CSV exports
│   └── urls.py                 # Admin management endpoints
├── static/                     # Static CSS, JavaScript, icons, and branding
├── templates/                  # Base layouts, email HTML templates, and component views
└── media/                      # Local development media fallback directory
```

## 4. Features
- **Multi-Step Reservation Funnel**: Location selection, date picker with client/server overlap verification, vehicle filtering, and checkout.
- **Dynamic Pricing Engine**: Automated daily rate computation with a 15% weekend surcharge across Friday, Saturday, and Sunday.
- **Multi-Gateway Payment Integration**: Stripe Checkout for card transactions and Razorpay Orders for UPI/NetBanking with cryptographic webhook verification.
- **Atomic Booking Integrity**: Concurrency protection utilizing `select_for_update()` during status updates and date overlap queries to prevent double-booking.
- **Passwordless OTP Authentication**: Phone number login via Twilio Verify API with automated account creation for new users.
- **Google OAuth 2.0 Single Sign-On**: Social authentication integration via Django-Allauth.
- **Automated Tax & Referral Accounting**: Automated GST calculations and atomic wallet credit allocation upon booking completion.
- **Transactional PDF Billing**: Automatic generation and email dispatch of PDF invoices and receipts via Resend/SMTP.
- **Executive Operations Dashboard**: Custom administrative portal for fleet inventory CRUD, booking approvals, cancellation overrides, and CSV audit reports.
- **Wishlist & Customer Reviews**: Vehicle favoriting and verified customer review submissions.

## 5. Database Design
- **UserProfile** (`accounts.models.UserProfile`)
  - `user`: OneToOneField (`auth.User`, on_delete=CASCADE, related_name='profile')
  - `phone`: CharField(max_length=15, db_index=True)
  - `profile_photo`: ImageField(upload_to='profiles/')
  - `date_of_birth`: DateField(null=True, blank=True)
  - `license_number`: CharField(max_length=50, blank=True)
  - `license_image`: ImageField(upload_to='licenses/', null=True, blank=True)
  - `aadhaar_number`: CharField(max_length=12, blank=True)
  - `pan_number`: CharField(max_length=10, blank=True)
  - `is_verified`: BooleanField(default=False)
  - `referral_code`: CharField(max_length=20, unique=True)
  - `referred_by`: ForeignKey('self', on_delete=SET_NULL, null=True, blank=True)
  - `wallet_balance`: DecimalField(max_digits=10, decimal_places=2, default=0)
  - `created_at`: DateTimeField(auto_now_add=True)

- **Car** (`core.models.Car`)
  - `name`: CharField(max_length=100)
  - `brand`: CharField(max_length=50, choices=BRAND_CHOICES)
  - `category`: CharField(max_length=20, choices=CATEGORY_CHOICES)
  - `price_per_day`: DecimalField(max_digits=8, decimal_places=2, db_index=True)
  - `security_deposit`: DecimalField(max_digits=10, decimal_places=2, default=0)
  - `free_km`: IntegerField(default=150)
  - `seats`: IntegerField(db_index=True)
  - `fuel_type`: CharField(max_length=30, db_index=True)
  - `transmission`: CharField(max_length=20)
  - `engine`: CharField(max_length=50)
  - `mileage`: CharField(max_length=30)
  - `image`: ImageField(upload_to='cars/', null=True, blank=True)
  - `is_available`: BooleanField(default=True)
  - `features`: JSONField(default=dict, blank=True)
  - `created_at`: DateTimeField(auto_now_add=True)

- **Booking** (`core.models.Booking`)
  - `user`: ForeignKey(`auth.User`, on_delete=CASCADE, related_name='bookings')
  - `car`: ForeignKey(`Car`, on_delete=CASCADE, related_name='bookings')
  - `booking_reference`: CharField(max_length=12, default='')
  - `pickup_date`: DateField()
  - `dropoff_date`: DateField()
  - `pickup_time`: TimeField(null=True, blank=True)
  - `dropoff_time`: TimeField(null=True, blank=True)
  - `pickup_location`: CharField(max_length=255, default='Main Office')
  - `dropoff_location`: CharField(max_length=255, default='Main Office')
  - `total_price`: DecimalField(max_digits=12, decimal_places=2)
  - `status`: CharField(max_length=20, choices=Status.choices, default='PENDING')
  - `stripe_session_id`: CharField(max_length=255, unique=True, null=True, blank=True)
  - `razorpay_order_id`: CharField(max_length=255, unique=True, null=True, blank=True)
  - `is_paid`: BooleanField(default=False)
  - `payment_intent_id`: CharField(max_length=255, null=True, blank=True)
  - `promo_code`: CharField(max_length=50, null=True, blank=True)
  - `discount_amount`: DecimalField(max_digits=10, decimal_places=2, default=0)
  - `is_outstation`: BooleanField(default=False)
  - `security_deposit`: DecimalField(max_digits=10, decimal_places=2, default=0)
  - `gst_amount`: DecimalField(max_digits=10, decimal_places=2, default=0)
  - `total_with_gst`: DecimalField(max_digits=10, decimal_places=2, default=0)
  - `gst_number`: CharField(max_length=15, null=True, blank=True)
  - `abandoned_reminder_sent`: BooleanField(default=False)
  - `created_at`: DateTimeField(auto_now_add=True)
  - `updated_at`: DateTimeField(auto_now=True)

- **Review** (`core.models.Review`)
  - `user`: ForeignKey(`auth.User`, on_delete=CASCADE, related_name='reviews')
  - `car`: ForeignKey(`Car`, on_delete=CASCADE, related_name='reviews')
  - `booking`: OneToOneField(`Booking`, on_delete=CASCADE, related_name='review')
  - `rating`: IntegerField(choices=1..5)
  - `comment`: TextField()
  - `created_at`: DateTimeField(auto_now_add=True)

- **Wishlist** (`core.models.Wishlist`)
  - `user`: ForeignKey(`auth.User`, on_delete=CASCADE, related_name='wishlists')
  - `car`: ForeignKey(`Car`, on_delete=CASCADE, related_name='wishlisted_by')
  - `created_at`: DateTimeField(auto_now_add=True)
  - Unique Constraint: `(user, car)`

- **PromoCode** (`core.models.PromoCode`)
  - `code`: CharField(max_length=20, unique=True)
  - `discount_type`: CharField(max_length=20, choices=['Percentage', 'Fixed'])
  - `discount_value`: DecimalField(max_digits=10, decimal_places=2)
  - `min_purchase`: DecimalField(max_digits=10, decimal_places=2, default=0)
  - `expiry_date`: DateTimeField()
  - `is_active`: BooleanField(default=True)
  - `usage_limit`: IntegerField(default=100)
  - `used_count`: IntegerField(default=0)

- **PushSubscription** (`core.models.PushSubscription`)
  - `user`: ForeignKey(`auth.User`, on_delete=CASCADE, related_name='push_subscriptions')
  - `subscription_info`: JSONField()
  - `created_at`: DateTimeField(auto_now_add=True)

- **Notification** (`core.models.Notification`)
  - `user`: ForeignKey(`auth.User`, on_delete=CASCADE, related_name='notifications')
  - `notification_type`: CharField(max_length=20, choices=['booking', 'payment', 'reminder', 'review', 'kyc', 'promo', 'system'])
  - `title`: CharField(max_length=200)
  - `message`: TextField()
  - `is_read`: BooleanField(default=False)
  - `is_archived`: BooleanField(default=False)
  - `action_url`: CharField(max_length=200, blank=True)
  - `created_at`: DateTimeField(auto_now_add=True)

## 6. API Endpoints
- GET / — Renders landing page with featured fleet and search interface — auth required: no
- GET /how-it-works/ — Renders informational onboarding workflow — auth required: no
- GET /cars/ — Catalog search and filter view with pagination — auth required: no
- GET /cars/<car_id>/ — Vehicle specification, feature breakdown, and verified reviews — auth required: no
- GET /booking/ — Step 1: Booking location and route selection — auth required: no
- GET /booking/<car_id>/ — Direct vehicle reservation entry point — auth required: no
- GET, POST /booking/dates/ — Step 2: Date range and availability selection — auth required: no
- GET, POST /booking/select/ — Step 3: Vehicle confirmation and outstation options — auth required: no
- GET, POST /booking/payment/ — Step 4: Checkout summary and gateway initiation — auth required: yes
- GET /booking/confirmation/<booking_id>/ — Booking confirmation page — auth required: yes
- GET /booking/invoice/<booking_id>/ — HTML invoice view — auth required: yes
- GET /booking/receipt/<booking_id>/ — Downloadable PDF receipt generation — auth required: yes
- GET /search/ — Search redirect and query handling — auth required: no
- GET, POST /contact/ — Contact inquiry submission — auth required: no
- POST /cars/<car_id>/review/ — Submit vehicle review and star rating — auth required: yes
- GET /api/cars/search/ — AJAX vehicle live search endpoint — auth required: no
- GET /api/booking/check-availability/ — JSON date collision checker — auth required: no
- POST /api/promo/apply/ — Promo code validation and discount calculation — auth required: no
- POST /api/wishlist/toggle/<car_id>/ — Add or remove car from user wishlist — auth required: yes
- GET /api/cars/<car_id>/booked-dates/ — Returns JSON array of booked dates for calendar disabling — auth required: no
- POST /api/stripe/webhook/ — Stripe webhook receiver for payment state synchronization — auth required: no
- POST /api/razorpay/callback/ — Razorpay payment verification callback handler — auth required: no
- GET /notifications/ — Notification center list view — auth required: yes
- POST /api/notifications/mark-read/<notification_id>/ — Mark single notification as read — auth required: yes
- POST /api/notifications/mark-all-read/ — Mark all user notifications as read — auth required: yes
- GET /api/notifications/count/ — JSON unread notification badge counter — auth required: yes
- GET /onboarding/ — New user onboarding view — auth required: yes
- GET /onboarding/skip/ — Skip onboarding flow — auth required: yes
- GET /login/ — Unified authentication page — auth required: no
- GET /signup/ — Signup redirection to unified login — auth required: no
- GET, POST /logout/ — User session termination — auth required: yes
- GET /dashboard/ — User dashboard overview with active bookings — auth required: yes
- GET /dashboard/bookings/ — Historical booking list with status filters — auth required: yes
- GET, POST /dashboard/profile/ — Profile information, KYC document upload, and password update — auth required: yes
- GET /dashboard/wishlist/ — Saved vehicles list — auth required: yes
- POST /login/otp/request/ — AJAX Twilio SMS OTP dispatch — auth required: no
- POST /login/otp/verify/ — AJAX Twilio OTP validation and session login — auth required: no
- GET /admin-panel/ — Executive fleet and booking metrics dashboard — auth required: yes (staff)
- GET /admin-panel/cars/ — Operational fleet inventory list — auth required: yes (staff)
- GET, POST /admin-panel/cars/add/ — Add new vehicle to fleet — auth required: yes (staff)
- GET, POST /admin-panel/cars/edit/<car_id>/ — Update vehicle details and pricing — auth required: yes (staff)
- POST /admin-panel/cars/delete/<car_id>/ — Remove vehicle from inventory — auth required: yes (staff)
- GET /admin-panel/bookings/ — Operations booking management table — auth required: yes (staff)
- POST /admin-panel/bookings/<booking_id>/status/ — Update booking status (Confirm, Complete, Cancel) — auth required: yes (staff)
- GET /admin-panel/bookings/csv/ — Export booking audit log to CSV format — auth required: yes (staff)
- GET /admin-panel/users/ — Registered customer directory — auth required: yes (staff)
- GET /admin-panel/revenue/ — Revenue analytics view — auth required: yes (staff)
- GET /api/admin/revenue/ — JSON analytics dataset for dashboard charts — auth required: yes (staff)
- GET /robots.txt — Search engine crawler rules — auth required: no
- GET /sitemap.xml — Dynamic XML sitemap for SEO — auth required: no

## 7. Authentication
Rentora supports three distinct authentication pathways:
1. **Phone Number OTP Login & Auto-Registration**: Users submit an Indian phone number (`+91...`). `TwilioService` initiates verification via Twilio Verify API. Upon client OTP submission, `otp_verify_login` verifies the code. If the phone number is not registered, an account is created atomically (`User` and `UserProfile`), automatically logging the user into a standard Django session.
2. **Google OAuth 2.0**: Integrated via `django-allauth`. Configured with `MySocialAccountAdapter` to automatically extract the user's profile and create an authenticated session upon successful token exchange.
3. **Session Authentication**: Standard Django username/email and password credential verification, managed via `django.contrib.auth`.

## 8. Key Engineering Decisions
- **Atomic Concurrency Protection via `select_for_update()`**:
  - *Problem*: High concurrency booking completions risked race conditions and inconsistent wallet balances during simultaneous checkout operations.
  - *Implementation*: `Booking.save()` wraps wallet reward updates inside `transaction.atomic()` using `Profile.objects.select_for_update()`.
  - *Rationale*: Locks the profile row at the database engine level until transaction commit, guaranteeing ledger consistency without lost updates.
- **Database-Level Overlap Queries & Indexed Lookups**:
  - *Problem*: Traditional date overlap validation in Python application memory allows race conditions where two users book the same vehicle concurrently.
  - *Implementation*: Enforced via `Booking.is_available_for_dates` and `Booking.check_overlap()` using SQL boundary filtering (`pickup_date__lte=dropoff_date, dropoff_date__gte=pickup_date`) against `['PENDING', 'CONFIRMED']` records. Multi-column composite database indexes were added on `[user, status]`, `[pickup_date]`, and `[is_paid]`.
  - *Rationale*: Pushes evaluation to the database engine index scan, reducing query overhead and preventing overlapping reservations.
- **Dual-Gateway Payment Orchestration with Cryptographic Verification**:
  - *Problem*: Indian market checkout requires UPI/NetBanking (Razorpay) alongside international credit cards (Stripe).
  - *Implementation*: Abstracted payment creation and verification into `BookingService`. Implemented HMAC-SHA256 signature verification for Razorpay callbacks and webhook payload signature verification for Stripe events.
  - *Rationale*: Separates payment provider logic from HTTP view controllers while ensuring idempotency and zero unauthorized order state transitions.
- **Cloud Object Storage via Supabase S3**:
  - *Problem*: Ephemeral filesystem storage on containerized hosting (Render) discards user-uploaded driving licenses and vehicle images on redeploy.
  - *Implementation*: Integrated `django-storages` with Boto3 configured against Supabase's S3-compatible object API endpoint, with local `FileSystemStorage` fallback during development.
  - *Rationale*: Ensures permanent cloud asset persistence and secure public asset distribution.
- **Proactive Sentry Telemetry Integration**:
  - *Problem*: Uncaught server exceptions and webhook processing failures in production can silently disrupt bookings.
  - *Implementation*: Configured `sentry_sdk` with Django integration in `settings.py`, capturing complete exception traces and performance timings.
  - *Rationale*: Enables real-time visibility into runtime anomalies and transaction failures.

## 9. Environment Variables
- `SECRET_KEY`: Django secret key for cryptographic signing and session security.
- `DEBUG`: Boolean flag controlling Django debug mode (`True` for local, `False` for production).
- `ALLOWED_HOSTS`: Comma-separated list of permitted hostnames and domain names.
- `DATABASE_URL`: Full PostgreSQL connection URI for production databases.
- `DB_NAME`: PostgreSQL database name (fallback when `DATABASE_URL` is omitted).
- `DB_USER`: PostgreSQL username.
- `DB_PASSWORD`: PostgreSQL user password.
- `DB_HOST`: PostgreSQL database host address.
- `DB_PORT`: PostgreSQL port (default: `5432` or `6543`).
- `STRIPE_PUBLIC_KEY`: Stripe publishable API key for frontend checkout.
- `STRIPE_SECRET_KEY`: Stripe secret API key for backend session generation.
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook signing secret for signature verification.
- `STRIPE_CURRENCY`: Currency code for Stripe transactions (e.g., `inr`).
- `RAZORPAY_KEY_ID`: Razorpay public key ID.
- `RAZORPAY_KEY_SECRET`: Razorpay secret API key for order generation and HMAC verification.
- `RESEND_API_KEY`: API key for Resend SMTP transactional email delivery.
- `DEFAULT_FROM_EMAIL`: Sender address for outgoing booking notifications and PDF receipts.
- `EMAIL_HOST`: Fallback SMTP server hostname (e.g., `smtp.gmail.com`).
- `EMAIL_PORT`: Fallback SMTP server port (e.g., `587`).
- `EMAIL_USE_TLS`: Boolean flag to enable TLS on fallback SMTP connections.
- `EMAIL_HOST_USER`: Fallback SMTP username.
- `EMAIL_HOST_PASSWORD`: Fallback SMTP password or application token.
- `SOCIAL_AUTH_GOOGLE_CLIENT_ID`: Google OAuth 2.0 client identifier.
- `SOCIAL_AUTH_GOOGLE_SECRET`: Google OAuth 2.0 client secret key.
- `VAPID_PUBLIC_KEY`: VAPID public key for Web Push notifications.
- `VAPID_PRIVATE_KEY`: VAPID private key for signing push notification payloads.
- `VAPID_ADMIN_EMAIL`: Contact email associated with VAPID registration.
- `GOOGLE_MAPS_API_KEY`: Google Maps JavaScript API key for location rendering.
- `SENTRY_DSN`: Sentry Data Source Name for production error monitoring.
- `TWILIO_ACCOUNT_SID`: Twilio account SID for SMS and Verify API integration.
- `TWILIO_AUTH_TOKEN`: Twilio authentication token.
- `AWS_ACCESS_KEY_ID`: S3 access key ID for Supabase cloud storage.
- `AWS_SECRET_ACCESS_KEY`: S3 secret key for Supabase cloud storage.
- `AWS_S3_ENDPOINT_URL`: Supabase S3-compatible API endpoint URL.
- `AWS_STORAGE_BUCKET_NAME`: Name of the Supabase storage bucket.
- `AWS_S3_REGION_NAME`: AWS/Supabase S3 storage region (default: `ap-south-1`).

## 10. Local Setup Instructions
Follow these steps to run Rentora locally:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/PranayaKD/Rentora.git
   cd Rentora
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file in the project root by copying the template:
   ```bash
   cp .env.example .env
   ```
   Provide valid local database credentials or development keys.

5. **Apply database migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create an administrative superuser**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Seed initial fleet data (optional)**:
   ```bash
   python manage.py loaddata cars.json
   ```

8. **Start the development server**:
   ```bash
   python manage.py runserver
   ```
   Access the application at `http://127.0.0.1:8000/`.
