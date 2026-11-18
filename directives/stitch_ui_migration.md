# Directive: Stitch UI Migration SOP

## Overview
This directive tracks the UI-only migration of the Rentora car rental platform from the Stitch export (`stitch_rentora_car_rental_app.zip` / Project `17120165524051866555`).
No backend features, models, migrations, or business logic are altered.

---

## Step 0: Audit Table (21 Screens)

| # | Stitch Screen | Target Template | Existing Django View / URL | Status |
|---|---|---|---|---|
| 1 | `rentora_home` | `templates/index.html` | `core:index` (`/`) | **WIRED to real data** |
| 2 | `rentora_car_listing` | `templates/cars.html` | `core:cars` (`/cars/`) | **WIRED to real data** |
| 3 | `rentora_filter_bottom_sheet` | `templates/cars.html` (component) | `core:cars` (`/cars/`) | **WIRED to real data** |
| 4 | `rentora_car_detail_maruti_swift` | `templates/car-detail.html` | `core:car_detail` (`/cars/<id>/`) | **WIRED to real data** |
| 5 | `rentora_booking_location_step_1_of_2` | `templates/booking-flow.html` | `core:booking_location` (`/booking/`) | **WIRED to real data** |
| 6 | `rentora_booking_dates_step_2_of_2` | `templates/booking-flow.html` | `core:booking_dates` (`/booking/dates/`) | **WIRED to real data** |
| 7 | `rentora_date_time_picker_bottom_sheet` | `templates/booking-flow.html` (component) | `core:booking_dates` (`/booking/dates/`) | **WIRED to real data** |
| 8 | `rentora_checkout_payment` | `templates/payment.html` | `core:payment` (`/booking/payment/`) | **WIRED to real data** |
| 9 | `rentora_booking_confirmed` | `templates/confirmation.html` | `core:confirmation` (`/booking/confirmation/<id>/`) | **WIRED to real data** |
| 10 | `rentora_my_bookings` | `templates/dashboard.html` | `accounts:dashboard_bookings` (`/dashboard/bookings/`) | **WIRED to real data** |
| 11 | `rentora_booking_details` | `templates/booking_detail.html` | `core:booking_detail` (`/booking/<id>/detail/`) | **WIRED to real data** |
| 12 | `rentora_cancel_booking_bottom_sheet` | `templates/components/cancel_sheet.html` | `core:cancel_booking` (`/booking/<id>/cancel/`) | **WIRED to real data** |
| 13 | `rentora_profile` | `templates/dashboard.html` (`#profile` tab) | `accounts:profile` (`/dashboard/profile/`) | **WIRED to real data** |
| 14 | `rentora_logout_confirmation_bottom_sheet`| `templates/components/logout_sheet.html` | `accounts:logout` (`/logout/`) | **WIRED to real data** |
| 15 | `rentora_login_phone_entry` | `templates/auth.html` | `accounts:login` (`/login/`) | **WIRED to real data** |
| 16 | `rentora_login_otp_entry` | `templates/auth.html` (step 2) | `accounts:login` (`/login/`) | **WIRED to real data** |
| 17 | `rentora_login_otp_error_state` | `templates/auth.html` (error state) | `accounts:login` (`/login/`) | **WIRED to real data** |
| 18 | `rentora_otp_login_bottom_sheet` | `templates/components/mobile_auth_modal.html` | `accounts:otp_login_request` / `accounts:otp_verify_login` | **WIRED to real data** |
| 19 | `rentora_driving_licence_kyc_upload` | `templates/onboarding.html` (upload state) | `core:onboarding` (`/onboarding/`) | **WIRED to real data** |
| 20 | `rentora_driving_licence_kyc_in_progress` | `templates/onboarding.html` (pending state) | `core:onboarding` (`/onboarding/`) | **WIRED to real data** |
| 21 | `rentora_driving_licence_kyc_verified` | `templates/onboarding.html` (verified state)| `core:onboarding` (`/onboarding/`) | **WIRED to real data** |

---

## Backend Handoff

### 1. Auth (`templates/auth.html`)
- **Template path**: `templates/auth.html`
- **Preview URL**: `/ui-preview/auth/`
- **Context variables expected**:
  - `phone`: str (e.g. `"+91 98765 43210"`)
  - `otp_error`: str (optional, e.g. `"Invalid OTP. 2 attempts remaining."`)
  - `resend_seconds`: int (e.g. `24`)
- **Forms / POST actions expected**:
  - Send OTP: `{% url 'otp_login_request' %}` submitting `phone`
  - Verify OTP: `{% url 'otp_verify_login' %}` submitting `phone`, `otp`
- **Hidden `{% if %}` blocks**:
  - `{% if allauth_google_enabled %}` for Google OAuth button
- **Done When**:
  - Wire `login_view` in `accounts/views.py` to handle full-page OTP flow and delete `/ui-preview/auth/` route and sample data.

### 2. Confirmation (`templates/confirmation.html`)
- **Template path**: `templates/confirmation.html`
- **Preview URL**: `/ui-preview/confirmation/`
- **Context variables expected**:
  - `booking.booking_reference`: str (e.g. `"RNT-982410"`)
  - `booking.car.name`: str (e.g. `"Maruti Swift ZXi"`)
  - `booking.car.image_url`: str
  - `booking.start_date`: datetime
  - `booking.end_date`: datetime
  - `booking.delivery_location`: str
  - `booking.total_price`: Decimal/float (e.g. `4648.00`)
- **Forms / POST actions expected**: None (Navigation buttons to `core:cars` and `accounts:dashboard_bookings`)
- **Hidden `{% if %}` blocks**:
  - `{% if booking.bluetooth_unlock %}` Bluetooth key CTA
- **Done When**:
  - `core:confirmation` view renders `confirmation.html` with real `booking` object. Delete `/ui-preview/confirmation/`.

### 3. Booking Detail (`templates/booking_detail.html`)
- **Template path**: `templates/booking_detail.html`
- **Preview URL**: `/ui-preview/booking_detail/`
- **Context variables expected**:
  - `booking.booking_reference`: str
  - `booking.status`: str (`"CONFIRMED"`, `"ACTIVE"`, `"COMPLETED"`, `"CANCELLED"`)
  - `booking.car`: Car object (`name`, `transmission`, `fuel_type`, `image_url`)
  - `booking.start_date`: datetime
  - `booking.end_date`: datetime
  - `booking.pickup_location`: str
  - `booking.dropoff_location`: str
  - `booking.plan_km`: int/str
  - `booking.base_fare`: Decimal
  - `booking.protection_fee`: Decimal
  - `booking.taxes`: Decimal
  - `booking.total_price`: Decimal
  - `booking.can_cancel`: bool
  - `refund_message`: str (e.g. `"Eligible for 100% refund until 2 hrs before pickup"`)
- **Forms / POST actions expected**:
  - Cancel booking: `{% url 'cancel_booking' booking.id %}`
- **Hidden `{% if %}` blocks**:
  - `{% if booking.can_cancel %}`
  - `{% if booking.can_extend %}`
  - `{% if booking.ends_in %}`
- **Done When**:
  - Create view `booking_detail_view` in `core` or `accounts`, add URL `booking/<int:id>/detail/`, delete `/ui-preview/booking_detail/`.

### 4. Cancel Sheet (`templates/components/cancel_sheet.html`)
- **Template path**: `templates/components/cancel_sheet.html`
- **Preview URL**: `/ui-preview/cancel_sheet/`
- **Context variables expected**:
  - `booking.id`: int
  - `booking.booking_reference`: str
  - `refund_message`: str (e.g. `"Full refund of ₹4,648 will be credited to original payment method in 3-5 days"`)
- **Forms / POST actions expected**:
  - POST to `{% url 'cancel_booking' booking.id %}` with CSRF token and `reason`
- **Hidden `{% if %}` blocks**:
  - `{% if refund_message %}`
- **Done When**:
  - Include inside `booking_detail.html` and wire `cancel_booking` POST handler. Delete preview route.

### 5. Logout Sheet (`templates/components/logout_sheet.html`)
- **Template path**: `templates/components/logout_sheet.html`
- **Preview URL**: `/ui-preview/logout_sheet/`
- **Context variables expected**:
  - `user.first_name` or `user.phone`: str
- **Forms / POST actions expected**:
  - POST to `{% url 'logout' %}`
- **Done When**:
  - Include inside `templates/dashboard.html` Profile tab. Delete preview route.

### 6. Onboarding / KYC (`templates/onboarding.html`)
- **Template path**: `templates/onboarding.html`
- **Preview URL**: `/ui-preview/onboarding/`
- **Context variables expected**:
  - `kyc_status`: str (`"upload"`, `"pending"`, `"verified"`)
  - `profile.license_number`: str (when pending or verified)
  - `profile.license_front_image`: Image URL
- **Forms / POST actions expected**:
  - POST to `{% url 'onboarding' %}` submitting `license_number` and `license_front` (enctype="multipart/form-data")
- **Hidden `{% if %}` blocks**:
  - `{% if kyc_status == 'upload' %}`
  - `{% if kyc_status == 'pending' %}`
  - `{% if kyc_status == 'verified' %}`
- **Done When**:
  - Wire `core:onboarding` to persist uploaded license image and number, delete `/ui-preview/onboarding/`.

---

## Token & Design Guide Notes
- Primary Teal: `#00C9A7` (button fills & active accents with dark `#050811` text).
- Primary Dark Teal: `#006b58` (only for teal text, icons, and borders on light backgrounds).
- Surface colors: `#f9f9ff` (background), `#ffffff` (container-lowest), `#f1f3ff` (container-low), `#e9edff` (container), `#151b2a` (on-surface text).
- Fonts: `Plus Jakarta Sans` (headlines & bold labels), `DM Sans` (body and regular labels), `Material Symbols Outlined` (icons).

---

## Shared Layout Architecture (Single Source)

1. **Base Shell (`templates/base.html`)**:
   - Single source for `components/navbar.html`, `components/bottom_nav.html`, `components/footer.html`, `components/city_modal.html`, `components/mobile_auth_modal.html`, and Django toast messages.
   - All duplicate navbar/footer markup across child templates has been removed.
2. **Context Processor (`core/context_processors.py`)**:
   - Registered under `TEMPLATES['OPTIONS']['context_processors']` as `core.context_processors.shared_layout_context`.
   - Provides:
     - `current_city`: Session-backed (`request.session.get('current_city', 'Bengaluru')`).
     - `is_authenticated`: Boolean flag.
     - `display_name`: Authenticated user's first name, profile name, or username.
     - `wishlist_count`: Real count of wishlisted cars for user.
     - `active_tab`: Dynamically resolved (`'home'`, `'search'`, `'bookings'`, `'profile'`).
     - `hide_bottom_nav`: Dynamically set to `True` on booking funnel, checkout, auth, and kyc routes.
3. **4-Tab Bottom Navigation (`components/bottom_nav.html`)**:
   - Exactly 4 tabs: Home (`/`), Search (`/cars/`), Bookings (`/accounts/dashboard/bookings/`), Profile (`/accounts/dashboard/`).
   - Anonymous users clicking Bookings or Profile are redirected to login with `?next=`.
   - Mobile-only (`md:hidden`), sticky with safe-area bottom padding.
4. **City Selection Endpoint (`/api/city/set/`)**:
   - Accepts POST with JSON `{"city": "<Name>"}` or form data.
   - Persists selection to `request.session['current_city']`.
   - Reflected dynamically in navbar across all pages.
5. **Static Legal & Support Routes**:
   - `/terms/`: `templates/legal/terms.html`
   - `/privacy/`: `templates/legal/privacy.html`
   - `/contact/`: `templates/contact.html` (Help & Support + contact query form)
6. **Automated Verification**:
   - `execution/test_shared_layout.py`: 44 automated checkpoints covering layout single-sourcing, active tab derivation, unauthenticated redirects with `?next=`, city session persistence, legal/support routes, full-page login, KYC lifecycle, and CSRF logout.
   - `execution/test_mobile_flows.py`: 44 reverse-engineered flow checkpoints (100% passing).

7. **Watermelon UI Component Upgrades & Scrollbar Removal**:
   - Replaced glowy cyan pill styling (`bg-accent text-primary shadow-lg shadow-accent/25`) with Watermelon UI / shadcn segmented control design:
     - Container: `inline-flex items-center gap-1 bg-zinc-950/80 backdrop-blur-xl p-1.5 rounded-2xl border border-white/10 mb-6 shadow-2xl max-w-full sm:max-w-xl w-full`.
     - Active Tab: High-contrast pure white pill `bg-white text-zinc-950 shadow-sm font-bold`.
     - Inactive Tab: `text-zinc-400 hover:text-white hover:bg-white/10 font-semibold`.
     - Delivery Preference: Segmented control with `peer-checked:bg-white peer-checked:text-zinc-950 peer-checked:shadow-sm`.
     - CTA Buttons: High-contrast `bg-zinc-950 text-white dark:bg-white dark:text-zinc-950` with subtle shadows, eliminating artificial neon blurs.
   - Fixed Windows native horizontal scrollbar by defining `.no-scrollbar` and `.hide-scrollbar` utilities in both `rentora.css` and `tailwind_input.css` with `::-webkit-scrollbar { display: none !important; width: 0 !important; height: 0 !important; }` and `-ms-overflow-style: none !important; scrollbar-width: none !important;` + Tailwind `[&::-webkit-scrollbar]:hidden [scrollbar-width:none] [-ms-overflow-style:none]`.
   - Restored and enhanced the Popular Brands infinite scrolling logo marquee:
     - 14 leading manufacturer logos (Maruti Suzuki, Hyundai, Tata, Mahindra, Toyota, Kia, BMW, Audi, Mercedes-Benz, Volkswagen, Skoda, Honda, MG, Porsche).
     - GPU-accelerated continuous right-to-left marquee animation (`translate3d(0,0,0)` to `translate3d(-50%,0,0)`).
     - Seamless loop with duplicated Set 1 and Set 2.
     - Gradient fade masks on left and right edges.
     - Pause-on-hover interaction for easy brand filtering.

8. **Car Card Refinement & Typography Overhaul**:
   - **Eliminated Grey-on-White Image Patch**: Replaced inner `bg-surface-container-low` (`#f1f3ff`) container with a clean `bg-white dark:bg-zinc-850/40` stage and added `mix-blend-multiply dark:mix-blend-normal` to `<img>`. The white cutout background of vehicle assets blends completely into the card surface with zero awkward rectangular borders.
   - **Crisp Quality & Scale Optimization**: Scaled the vehicle container from `h-44 sm:h-52` (208px high stretching 300x168 images) down to `h-32 sm:h-36` (128-144px). Added hardware-accelerated crisp rendering rules (`image-rendering: -webkit-optimize-contrast; crisp-edges; transform: translateZ(0);`) in `rentora.css`.
   - **Compact Card Dimensions**: Decreased card padding from `p-4` to `p-3 sm:p-3.5`, rounded corners from `rounded-3xl` to `rounded-2xl`, and adjusted desktop section grid gaps from `gap-12` (48px) to `gap-5 sm:gap-6` across Budget, Mid-Range, Luxury, and Electric sections.
   - **Bold Typography Formatting**: Overhauled all card typography with high-contrast bold weights (`font-black` / `font-bold`):
     - Brand: `text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-zinc-500`
     - Car Title: `text-sm sm:text-base font-black text-slate-900 dark:text-white leading-tight`
     - Badges: `text-[10px] font-black uppercase tracking-wider`
     - Specs (Transmission, Fuel, Seats): `font-bold text-[11px] text-slate-800 dark:text-zinc-200 bg-slate-100 dark:bg-zinc-800/80 px-2 py-0.5 rounded-md`
     - Pricing: `text-lg sm:text-xl font-black text-slate-900 dark:text-white`
     - Rent Now CTA: `font-black text-xs uppercase tracking-wider bg-zinc-950 text-white dark:bg-white dark:text-zinc-950 px-4 py-2 rounded-xl`




9. **Watermelon Theme & UI Polish**:
   - **Hero Wavy Underline**: Updated "Freedom" text decoration from legacy green to vibrant Watermelon Coral (`#FF385C` / `decoration-[#FF385C] decoration-wavy decoration-[3px] underline-offset-8`).
   - **Color System Modernization**: Updated `:root` tokens and `tailwind.config.js` to map `--primary` and `--accent` to Watermelon Coral (`#FF385C`), with high-contrast text and zero neon glare.
   - **Product Mode Segmented Tabs**: Fixed native Windows horizontal scrollbar with `sm:overflow-visible`, `-ms-overflow-style: none`, `scrollbar-width: none`, and explicit WebKit scrollbar pseudo-element removal. Active tab styled in crisp Watermelon Coral with bold white typography.
   - **Car Card Polish**: Integrated Watermelon UI accent highlights (`#FF385C` on hover and badges) while maintaining compact dimensions and zero image box clipping (`mix-blend-multiply`).

10. **PostgreSQL & Production Deployment Architecture**:
    - **Fleet Store Filter Shift Fixed**: Separated `#desktop-filter-sidebar` (permanently docked left inside `flex-row items-start`) from `#mobile-filter-drawer` (strictly `md:hidden`), eliminating rightward filter drift when clearing filters.
    - **Production Error Handlers**: Created custom branded `templates/404.html` and `templates/500.html`.
    - **PostgreSQL Setup Tool**: Implemented `Rentora/execution/setup_postgres.py` for automated connection verification, migrations, fleet seeding, and ACID transaction lock testing.
    - **Security Verification**: Configured `CSRF_TRUSTED_ORIGINS` and `SECURE_SSL_REDIRECT`. All 88 automated tests passing (44/44 shared layout, 44/44 mobile flows).
