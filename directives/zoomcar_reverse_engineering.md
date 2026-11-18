# Directive: Zoomcar Reverse-Engineering & Mobile-First Architecture for Rentora

## 1. Objective
Reverse-engineer the complete user experience, booking funnel, pricing logic, and mobile-first interface of Zoomcar (https://www.zoomcar.com/) and implement it seamlessly into **Rentora** (Automotive Fleet Rental & Booking Engine) under the Rentora brand.

## 2. Brand Identity: Rentora
- **Brand Name**: Rentora
- **Primary Color Palette**:
  - Accent / Primary CTA: Emerald / Neon Teal (`#00c9a7`)
  - Midnight Canvas: `#050811` / `#09090b` / `#0a0f1f`
  - Card & Surface: `#ffffff` (light mode), `#14161e` (dark mode)
  - Typography: Plus Jakarta Sans / DM Sans
- **Tagline**: "Self-Drive Freedom, Delivered to Your Doorstep."
- **Core Value Propositions**:
  - 100% Freedom (Keyless unlock, zero queues, zero awkward handovers)
  - Doorstep Delivery (Anywhere, anytime at your home, hotel, or airport)
  - Transparent Pricing (Zero hidden charges, dynamic KM packages, zero deposit options)
  - Verified Fleet & Super Hosts (Quality-checked cars with 24/7 roadside assistance)

## 3. Zoomcar Feature Set Mapped to Rentora

### A. Discovery & Homepage
1. **City & Hub Selector**:
   - Top city switcher bottom sheet on mobile (Bangalore, Mumbai, Delhi NCR, Hyderabad, Pune, Goa, Chennai, Kolkata, etc.)
   - Instant filtering based on selected city.
2. **Rental Mode Switcher Tabs**:
   - **Daily Drives**: Short duration trips (hourly or daily, 1-7 days).
   - **Subscription / Long Term**: Extended rental options (7+ days).
   - **Weekday Commute Pass**: Mon-Fri city travel.
   - **Outstation / Chauffeur**: Long distance road trips with driver option.
3. **Mobile-First Search Capsule**:
   - Pickup Location / Landmark autocomplete (with airport & hub shortcuts)
   - Date & Time pickers with live trip duration calculator (e.g., "24 hrs / 1 Day")
   - Delivery Mode toggle: "Doorstep Delivery" vs "Self Pickup"
4. **Trust Tickers & Social Proof**:
   - "✨ 25,000+ Top Rated Cars ✨"
   - "4.8★ Average Rating | 25M+ Happy Trips"
   - "Verified Fleet & 100% Insured"
5. **How It Works (5-Step Journey)**:
   - Search -> Compare KM Plans -> Book with instant confirmation -> Quick 2-min KYC -> Drive & Return.

### B. Search & Fleet Catalog (Mobile-First Experience)
1. **Sticky Search Header**:
   - City and Landmark pill
   - Trip duration badge (e.g., "4 Nov 7:00 PM → 5 Nov 7:00 PM")
   - Inline search bar for make, model, features
   - Sort by trigger
2. **Horizontal Quick Filter Pills**:
   - Scrollable filter bar: `[ Filters  ]`, `[ Super Host ]`, `[ Doorstep Delivery ]`, `[ Guest Favorite ]`, `[ SUV ]`, `[ 6/7 Seater ]`, `[ Automatic ]`, `[ 4.5+ Rated ]`, `[ Diesel ]`, `[ Electric ]`
3. **Floating KM Package Switcher (The Zoomcar Signature)**:
   - Sticky mobile pill at bottom: `[ ⚡ Unlimited Kms ]` | `[ 🚗 300 Kms incl. ]`
   - Toggling updates hourly rates and total trip prices dynamically across all car cards!
4. **Zoomcar-Style Car Card Anatomy**:
   - Multi-image swipeable gallery with pagination dots
   - Badges: "Guest Favorite" / "Top Rated" / "Super Host"
   - Heart icon wishlist toggle (instant AJAX)
   - Title & Transmission / Fuel / Seats badges (`Manual` • `Petrol` • `5 Seats`)
   - Distance & Delivery info (`📍 2.4 km away • Doorstep Delivery Available`)
   - Pricing display:
     - Hourly rate: `₹80/hr`
     - Total trip rate: `₹1,920 excluding fees` with clickable info icon
   - "Book Now" CTA
5. **Filter Bottom Sheet Drawer**:
   - Drag handle, touch-friendly dismiss
   - Sort By (Highest Rated, Price Low-High, Price High-Low, Distance)
   - Distance slider (0-30 km)
   - Delivery type toggle (Doorstep vs Hub)
   - Price range slider
   - Car category, fuel type, transmission, seating capacity filters

### C. Fare Breakup Bottom Sheet
- Tapping on car card price or detail page opens a transparent breakdown:
  - Base Rental Fare (Rate x Duration)
  - KM Inclusion Plan (300 km or Unlimited)
  - Extra KM charges (₹7/km)
  - Damage Protection Cover options (Standard vs Premium Zero Liability)
  - Convenience Fee & 18% GST calculation
  - Refundable Security Deposit (₹0 or nominal)
  - Fuel Policy notice: "Fuel not included. Return at same level."

### D. Mobile Phone OTP Auth Drawer
- When unauthenticated users click "Book Now", trigger a mobile slide-up sheet:
  - Phone input with +91 country prefix
  - Instant OTP delivery via Twilio API
  - 6-digit code entry with auto-submit
  - Immediate authentication without redirect or losing selected car/dates!

### E. Car Detail & Sticky Checkout Bar
- Full-screen swipeable image carousel
- Vehicle specifications & performance highlights
- Host verification profile card
- Damage Protection Cover selection
- Sticky Bottom Action Bar with Total Price + "Proceed to Pay" CTA

### F. Native App-like Navigation
- Fixed 5-tab bottom navigation bar:
  - Home, Search, Bookings, Alerts, Profile
- Safe-area-bottom padding for modern bezel-less smartphones.

## 4. Execution Tools
- `execution/seed_zoomcar_fleet.py`: Seed realistic fleet matching Zoomcar popular models (Swift, Punch, Baleno, Thar 4x4, Creta, Scorpio-N, Innova Crysta, Nexon EV). Total 92 vehicles.
- `execution/test_mobile_flows.py`: Complete deterministic verification test suite covering 44 checkpoints:
  - Homepage, City modal, Product modes, Trust ticker, Journey steps.
  - "Explore by Category" 6-card grid (Hatchback, SUV, 7-Seater, EV, Sedan, Luxury) & Brand quick chips.
  - Search catalog, Floating KM package switcher, Filter drawer, Category & Transmission filtering.
  - Seamless AJAX filter updates without full-page reloads.
  - Car detail page, Damage protection, Doorstep delivery, Mobile sticky booking bar.
  - Touch-swipeable multi-image car gallery & 3 Zoomcar trust badges (₹0 Deposit, Same-to-Same Fuel, Free Cancellation).
  - In-page Mobile OTP auth drawer, verification & auto-signup.
  - Hourly & daily price calculations (both 300 km and Unlimited packages).
  - Streamlined 1-tap booking flow (same dropoff default, optional toggle for different dropoff).
  - Leaflet map with Esri World Street Map tiles (no API key required, zero watermarks).
  - Dynamic live trip duration counter pill in Step 2.
  - Payment checkout page, KM Plan & Fuel Policy items, Damage protection cover, Mobile sticky checkout bar.
  - In-page promo code recalculation without page reload.

## 5. Self-Annealing Learnings
1. **Python Path**: Always invoke `C:\Users\dashp\AppData\Local\Programs\Python\Python311\python.exe` which contains all required Django 5, Stripe, Razorpay, and Twilio packages.
2. **Local Database**: Use `USE_LOCAL_DB=True` fallback to SQLite (`db.sqlite3`) for fast, zero-dependency sandboxed execution and deterministic testing.
3. **Template Context in Tests**: In standalone Django test scripts, call `from django.test.utils import setup_test_environment; setup_test_environment()` to ensure template context lists are fully populated in test responses.
4. **URL Routing Parity**: Mount `/auth/` and `/accounts/` routes in addition to root routes in `rentora_project/urls.py` so both `/login/otp/...` and `/auth/login/otp/...` and `/accounts/dashboard/...` resolve reliably.
5. **Tile Provider Reliability**: Use Esri World Street Map tiles (`https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}`) for Leaflet to eliminate OSM volunteer-server blocking and CartoDB API key watermarks.
6. **Mobile Viewport Optimization**: Ensure sticky bottom checkout bars and touch targets have `safe-area-bottom` padding, hide global bottom tab bar on booking and payment steps to avoid click interception, and perform seamless in-page promo calculations.

