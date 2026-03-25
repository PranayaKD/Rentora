# 🏎️ Rentora: High-Performance Rental Ecosystem

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Rentora** is a production-hardened, executive-grade car rental platform designed specifically for the modern Indian market. Built with a focus on **atomic reliability**, **premium UX**, and **cloud-native scalability**, it transforms the complex rental workflow into a frictionless digital experience.

---

## ✨ Key Features

### 🛡️ Atomic Booking Engine
-   **No Double Bookings**: Implements `select_for_update()` at the database level to prevent race conditions during peak hours.
-   **Overlap Prevention**: Custom logic ensures no vehicle can be booked for conflicting time slots, even across multiple timezones.
-   **Abandoned Cart Recovery**: Automatically tracks pending bookings and recovers lost revenue through timed reminders.

### 💎 Premium User Experience
-   **Glassmorphism UI**: A stunning, modern interface built with **Tailwind CSS** and **GSAP** micro-animations.
-   **Interactive Location Discovery**: Real-time city and location suggestions with a sleek, interactive search experience.
-   **PWA Ready**: Installable on mobile devices for a native-app feel, featuring offline caching and push notifications.

### 📊 Rentora HQ (Executive Dashboard)
-   **Real-time Analytics**: Built-in revenue and fleet monitoring using **ApexCharts**.
-   **Fleet Management**: Full CRUD capabilities for cars, categories, and brands with dynamic pricing controls.
-   **Weekend Surcharge Engine**: Automatically applies a 15% surcharge for weekend bookings to maximize yield.

### 🛡️ Production-Grade Infrastructure
-   **Cloud Media (Supabase S3)**: All vehicle and user assets are served via Supabase's S3-compatible cloud storage for maximum persistence.
-   **Professional Monitoring (Sentry)**: Real-time error tracking and performance monitoring to catch bugs before users do.
-   **Secure Payments (Stripe)**: Seamless, secure checkout with automatic GST calculation and tax invoicing.
-   **Verified Email (Resend)**: Industry-standard transactional email delivery for confirmations and professional HTML invoices.

---

## 🛠️ Tech Stack

-   **Backend**: Django 5.2.4 (Python 3.13)
-   **Frontend**: Vanilla HTML/JS, Tailwind CSS, GSAP (Animations)
-   **Database**: PostgreSQL (Supabase)
-   **Storage**: Supabase S3 (Digital Assets)
-   **Payments**: Stripe API
-   **Email**: Resend SMTP Relay
-   **Monitoring**: Sentry SDK
-   **Notifications**: Twilio (OTP/WhatsApp)

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/PranayaKD/Rentora.git
cd Rentora
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy the template and fill in your actual credentials:
```bash
cp .env.example .env
```
*Make sure to update your `STRIPE_SECRET_KEY`, `RESEND_API_KEY`, and `SENTRY_DSN` in the `.env` file.*

### 3. Initialize Database
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run Development Server
```bash
python manage.py runserver
```

---

## 📦 Deployment & Monitoring

### Media Migration
To sync your local car images to the cloud (Supabase S3), run our custom migration command:
```bash
python manage.py migrate_media
```

### Sentry Verification
Verify your monitoring setup by visiting:
`http://localhost:8000/sentry-debug/`

---

## 🛡️ License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact
**Pranaya K D** - [GitHub](https://github.com/PranayaKD)

---
*Created with ❤️ for the Indian Rental Market.*
