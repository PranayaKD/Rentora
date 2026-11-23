/**
 * Rentora Global JS
 */

document.addEventListener('DOMContentLoaded', () => {

    // --- Mobile Auto-Prompt for Odisha Location ---
    initMobileLocationAutoPrompt();

    // --- Toast Notification System ---
    const toasts = document.querySelectorAll('[data-toast]');
    toasts.forEach((toast, index) => {
        // Trigger entry animation with slight stagger
        setTimeout(() => {
            toast.classList.remove('translate-x-full', 'opacity-0');
            toast.classList.add('translate-x-0', 'opacity-100');
        }, 100 * (index + 1));

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            dismissToast(toast);
        }, 5000 + (100 * index));
    });

    // --- Nav Active State Highlighting ---
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.bottom-nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href !== '/' && currentPath.includes(href)) {
            // Remove text-slate-500, add text-accent
            link.classList.remove('text-slate-500', 'dark:text-slate-400');
            link.classList.add('text-accent', 'dark:text-accent');
            
            // Fill icon if applicable
            const icon = link.querySelector('.material-symbols-outlined');
            if (icon) {
                icon.style.fontVariationSettings = "'FILL' 1";
            }
        } else if (href === '/' && currentPath === '/') {
            link.classList.remove('text-slate-500', 'dark:text-slate-400');
            link.classList.add('text-accent', 'dark:text-accent');
            const icon = link.querySelector('.material-symbols-outlined');
            if (icon) {
                icon.style.fontVariationSettings = "'FILL' 1";
            }
        }
    });

    // --- Scroll Reveal Animation Engine ---
    initScrollReveal();
    initCountUp();
    initStickyPin();
    initHeaderMorph();
    initScrollScrubText();
    initStackingCards();
    initToastNotifications();
    // initCarousels handled by dedicated banner carousel component

});

/**
 * Header Morph on Scroll
 * Transforms the fixed top navigation bar into a frosted floating dock
 */
function initHeaderMorph() {
    const header = document.getElementById('main-header');
    if (!header) return;

    let ticking = false;
    const onScroll = () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                if (window.scrollY > 40) {
                    header.classList.add('header-scrolled');
                } else {
                    header.classList.remove('header-scrolled');
                }
                ticking = false;
            });
            ticking = true;
        }
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    if (window.scrollY > 40) {
        header.classList.add('header-scrolled');
    }
}

/**
 * Apple-style Scroll Scrubbed Text Reveal Engine
 * Progressively illuminates words from muted slate to crisp high-contrast dark as reader scrolls
 */
function initScrollScrubText() {
    const scrubContainers = document.querySelectorAll('.scroll-scrub-text');
    if (!scrubContainers.length) return;

    scrubContainers.forEach(container => {
        if (container.getAttribute('data-scrub-ready') === 'true') return;
        const text = container.textContent.trim();
        const words = text.split(/\s+/);
        container.innerHTML = words.map(w => `<span class="scrub-word">${w}</span>`).join(' ');
        container.setAttribute('data-scrub-ready', 'true');
    });

    let ticking = false;
    const updateScrub = () => {
        const windowHeight = window.innerHeight;
        scrubContainers.forEach(container => {
            const rect = container.getBoundingClientRect();
            const words = container.querySelectorAll('.scrub-word');
            if (!words.length) return;

            const triggerStart = windowHeight * 0.85;
            const triggerEnd = windowHeight * 0.35;
            
            // One-time progressive reveal: only illuminates forward, NEVER un-illuminates on scroll back up
            if (rect.top <= triggerStart) {
                if (rect.bottom < triggerEnd) {
                    words.forEach(w => w.classList.add('is-illuminated'));
                } else {
                    const progress = Math.max(0, Math.min(1, (triggerStart - rect.top) / (triggerStart - triggerEnd)));
                    const activeCount = Math.floor(progress * words.length);
                    words.forEach((w, idx) => {
                        if (idx <= activeCount) {
                            w.classList.add('is-illuminated');
                        }
                    });
                }
            }
        });
        ticking = false;
    };

    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(updateScrub);
            ticking = true;
        }
    }, { passive: true });

    updateScrub();
}

function initScrollReveal() {
    // 1. Process Staggered Word-by-Word Float elements
    const wordFloatElements = document.querySelectorAll('.reveal-word-float');
    wordFloatElements.forEach(el => {
        // Skip if already tokenized
        if (el.getAttribute('data-words-ready') === 'true') return;
        const text = el.innerText.trim();
        const words = text.split(/\s+/);
        el.innerHTML = words.map((w, idx) => {
            const delay = Math.min(idx * 35, 600);
            return `<span class="word-span" style="transition-delay: ${delay}ms;">${w}&nbsp;</span>`;
        }).join('');
        el.setAttribute('data-words-ready', 'true');
    });

    const revealElements = document.querySelectorAll(
        '.reveal-on-scroll, .reveal-fade-in, .reveal-scale-up, .reveal-slide-left, .reveal-slide-right, .reveal-mask-heading, .reveal-word-float, .marker-sweep, .reveal-blur-focus, .reveal-stagger, .reveal-lines, .reveal-card-stagger, .stacking-card, .stacking-cards-container'
    );

    if (!revealElements.length || !('IntersectionObserver' in window)) return;

    // Enable reveal CSS animations only when observer is supported & ready
    document.documentElement.classList.add('js-reveal-active');

    const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-revealed');
                obs.unobserve(entry.target);
            }
        });
    }, {
        root: null,
        rootMargin: '0px 0px -30px 0px',
        threshold: 0.05
    });

    revealElements.forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.top < window.innerHeight && rect.bottom > 0) {
            el.classList.add('is-revealed');
        } else {
            observer.observe(el);
        }
    });
}

/**
 * Dynamic Numeric Roll Ticker Engine
 * Smooth easeOutExpo numeric counter for trust metrics
 */
function initCountUp() {
    const stats = document.querySelectorAll('.count-up-stat');
    if (!stats.length || !('IntersectionObserver' in window)) return;

    const animateNumber = (el) => {
        const rawTarget = el.getAttribute('data-target') || el.innerText.replace(/[^0-9.]/g, '');
        const target = parseFloat(rawTarget);
        if (isNaN(target)) return;

        const decimals = parseInt(el.getAttribute('data-decimals') || '0', 10);
        const prefix = el.getAttribute('data-prefix') || '';
        const suffix = el.getAttribute('data-suffix') || '';
        const isComma = el.getAttribute('data-format') === 'comma';
        const duration = 1600; // ms
        const startTime = performance.now();

        const formatVal = (val) => {
            let str = val.toFixed(decimals);
            if (isComma && decimals === 0) {
                str = Math.round(val).toLocaleString('en-IN');
            }
            return `${prefix}${str}${suffix}`;
        };

        const updateTick = (now) => {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // easeOutExpo
            const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
            const current = target * ease;
            el.textContent = formatVal(current);

            if (progress < 1) {
                requestAnimationFrame(updateTick);
            } else {
                el.textContent = formatVal(target);
            }
        };

        requestAnimationFrame(updateTick);
    };

    const counterObserver = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateNumber(entry.target);
                obs.unobserve(entry.target);
            }
        });
    }, {
        root: null,
        threshold: 0.1
    });

    stats.forEach(s => {
        const rect = s.getBoundingClientRect();
        if (rect.top < window.innerHeight && rect.bottom > 0) {
            animateNumber(s);
        } else {
            counterObserver.observe(s);
        }
    });
}

/**
 * Sticky Filter Pin & Elevation Shadow
 */
function initStickyPin() {
    const stickyEls = document.querySelectorAll('.sticky-filter-pin');
    if (!stickyEls.length) return;

    window.addEventListener('scroll', () => {
        stickyEls.forEach(el => {
            const rect = el.getBoundingClientRect();
            // When sticking near top (within 90px of top header)
            if (rect.top <= 85) {
                el.classList.add('is-pinned');
            } else {
                el.classList.remove('is-pinned');
            }
        });
    }, { passive: true });
}

function dismissToast(element) {
    if(!element) return;
    element.style.opacity = '0';
    element.style.transform = 'translateY(-10px)';
    setTimeout(() => {
        element.remove();
    }, 300);
}

// Global utility for AJAX Wishlist toggle
window.toggleWishlist = function(carId, btnElement) {
    if (window.event) {
        window.event.preventDefault();
        window.event.stopPropagation();
    }
    
    // If not authenticated, immediately prompt login via Mobile Auth Modal
    if (!window.rentoraIsAuthenticated) {
        if (typeof openMobileAuthModal === 'function') {
            openMobileAuthModal('login', carId);
        } else {
            window.location.href = `/accounts/login/?next=${encodeURIComponent(window.location.pathname)}`;
        }
        return;
    }

    const csrftoken = getCookie('csrftoken') || '';
    const icon = btnElement ? btnElement.querySelector('.material-symbols-outlined') : null;

    fetch(`/api/wishlist/toggle/${carId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json'
        }
    })
    .then(res => {
        if (res.status === 401 || res.status === 403 || res.redirected) {
            if (typeof openMobileAuthModal === 'function') {
                openMobileAuthModal('login', carId);
            }
            return null;
        }
        return res.json();
    })
    .then(data => {
        if (!data || !icon) return;
        if (data.wishlisted || data.status === 'added') {
            icon.style.fontVariationSettings = "'FILL' 1";
            icon.classList.add('text-red-500', 'fill');
            icon.classList.remove('text-slate-700');
        } else {
            icon.style.fontVariationSettings = "'FILL' 0";
            icon.classList.remove('text-red-500', 'fill');
            icon.classList.add('text-slate-700');
        }
    })
    .catch(err => {
        console.error("Wishlist error:", err);
    });
};

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Global Car Booking Action Handler
 */
window.handleCarBookClick = function(carId) {
    if (window.rentoraIsAuthenticated) {
        window.location.href = `/booking/${carId}/`;
    } else if (typeof openMobileAuthModal === 'function') {
        openMobileAuthModal(carId);
    } else {
        window.location.href = `/login/?next=/booking/${carId}/`;
    }
};

window.goToCarDetail = function(carId) {
    window.location.href = `/cars/${carId}/`;
};

/**
 * Carousel delegation hooks
 * Dedicated banner carousels manage their own lifecycle and infinite loops.
 */
function initCarousels() {
    // No-op: Carousels self-initialize via components/promo_banner_carousel.html
}

/**
 * Coming Soon Popup Modal Handler
 */
window.openComingSoonModal = function(title = 'Coming Soon', platform = '') {
    const modal = document.getElementById('coming-soon-modal');
    const panel = document.getElementById('coming-soon-panel');
    const titleEl = document.getElementById('coming-soon-title');
    const descEl = document.getElementById('coming-soon-desc');

    if (!modal) return;

    if (platform && titleEl && descEl) {
        titleEl.textContent = `${title} Launching Soon`;
        descEl.textContent = `Our official app for ${platform} is in pilot testing with Odisha drivers. Keyless smartphone unlock, instant booking, and automated FASTag tracking will be available soon.`;
    }

    modal.classList.remove('opacity-0', 'pointer-events-none');
    modal.classList.add('opacity-100');
    if (panel) {
        panel.classList.remove('scale-95');
        panel.classList.add('scale-100');
    }
    document.body.style.overflow = 'hidden';
};

window.closeComingSoonModal = function() {
    const modal = document.getElementById('coming-soon-modal');
    const panel = document.getElementById('coming-soon-panel');
    if (!modal) return;

    modal.classList.add('opacity-0', 'pointer-events-none');
    modal.classList.remove('opacity-100');
    if (panel) {
        panel.classList.add('scale-95');
        panel.classList.remove('scale-100');
    }
    document.body.style.overflow = '';
};

// Close modal when clicking backdrop
document.addEventListener('click', (e) => {
    const modal = document.getElementById('coming-soon-modal');
    if (modal && e.target === modal) {
        window.closeComingSoonModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const modal = document.getElementById('coming-soon-modal');
        if (modal && !modal.classList.contains('opacity-0')) {
            window.closeComingSoonModal();
        }
    }
});



/**
 * Stacking Cards Dynamic Depth & Scale Engine
 * Progressively scales and darkens underlying cards as subsequent cards slide over
 */
function initStackingCards() {
    const containers = document.querySelectorAll('.stacking-cards-container');
    if (!containers.length) return;

    let ticking = false;
    const updateStack = () => {
        containers.forEach(container => {
            const cards = container.querySelectorAll('.stacking-card');
            cards.forEach((card, idx) => {
                if (idx === cards.length - 1) return;
                const nextCard = cards[idx + 1];
                if (!nextCard) return;

                const nextRect = nextCard.getBoundingClientRect();
                const cardRect = card.getBoundingClientRect();

                if (nextRect.top < cardRect.bottom) {
                    const overlap = Math.max(0, Math.min(1, (cardRect.bottom - nextRect.top) / cardRect.height));
                    const scale = (1 - (overlap * 0.05)).toFixed(3);
                    const brightness = (1 - (overlap * 0.06)).toFixed(3);
                    card.style.transform = `scale(${scale}) translateZ(0)`;
                    card.style.filter = `brightness(${brightness})`;
                } else {
                    card.style.transform = 'scale(1) translateZ(0)';
                    card.style.filter = 'brightness(1)';
                }
            });
        });
        ticking = false;
    };

    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(updateStack);
            ticking = true;
        }
    }, { passive: true });
}

/**
 * Mobile Auto-Prompt for Odisha Location
 * Automatically prompts the user for their location / hub on first mobile visit
 */
function initMobileLocationAutoPrompt() {
    if (window.innerWidth < 768) {
        const prompted = sessionStorage.getItem('rentora_mobile_location_prompted');
        if (!prompted) {
            sessionStorage.setItem('rentora_mobile_location_prompted', 'true');
            setTimeout(() => {
                if (typeof openCityModal === 'function') {
                    openCityModal();
                }
            }, 800);
        }
    }
}

/**
 * Toast Notification System
 * Auto-dismisses after 2.0s with interactive progress indicator & manual close
 */
function initToastNotifications() {
    const toasts = document.querySelectorAll('[data-toast]');
    toasts.forEach(toast => setupToastElement(toast));
}

function setupToastElement(toast) {
    if (!toast || toast.dataset.initialized === 'true') return;
    toast.dataset.initialized = 'true';

    const duration = parseInt(toast.dataset.duration || '2000', 10);
    const progressBar = toast.querySelector('.toast-progress-bar');

    // Entry animation
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px) scale(0.96)';
    requestAnimationFrame(() => {
        toast.style.transition = 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)';
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0) scale(1)';
        if (progressBar) {
            progressBar.style.transition = `width ${duration}ms linear`;
            progressBar.style.width = '0%';
        }
    });

    let dismissTimer = null;
    let startTime = Date.now();
    let remaining = duration;

    const startTimer = () => {
        startTime = Date.now();
        dismissTimer = setTimeout(() => {
            dismissToast(toast);
        }, remaining);
    };

    const pauseTimer = () => {
        if (dismissTimer) {
            clearTimeout(dismissTimer);
            dismissTimer = null;
            remaining -= (Date.now() - startTime);
            if (progressBar) {
                const currentWidth = (remaining / duration) * 100;
                progressBar.style.transition = 'none';
                progressBar.style.width = `${Math.max(0, currentWidth)}%`;
            }
        }
    };

    // Pause on hover so user can read if needed
    toast.addEventListener('mouseenter', pauseTimer);
    toast.addEventListener('mouseleave', () => {
        if (remaining > 0) {
            if (progressBar) {
                progressBar.style.transition = `width ${remaining}ms linear`;
                progressBar.style.width = '0%';
            }
            startTimer();
        } else {
            dismissToast(toast);
        }
    });

    startTimer();
}

function dismissToast(toast) {
    if (!toast || toast.dataset.dismissing === 'true') return;
    toast.dataset.dismissing = 'true';
    toast.style.transition = 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-8px) scale(0.94)';
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 260);
}
window.dismissToast = dismissToast;

/**
 * Programmatic showToast API for client-side actions
 */
window.showToast = function(message, type = 'info', duration = 2000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed top-22 sm:top-24 right-3 sm:right-6 left-3 sm:left-auto z-[100] flex flex-col gap-2.5 w-auto sm:w-[380px] pointer-events-none';
        container.setAttribute('aria-live', 'polite');
        document.body.appendChild(container);
    }

    const typeConfig = {
        success: {
            border: 'border-emerald-500/40',
            iconBg: 'bg-emerald-500/15 text-emerald-600',
            icon: 'check_circle',
            progressBg: 'bg-emerald-500'
        },
        error: {
            border: 'border-red-500/40',
            iconBg: 'bg-red-500/15 text-red-600',
            icon: 'error',
            progressBg: 'bg-red-500'
        },
        warning: {
            border: 'border-[#D9541E]/40',
            iconBg: 'bg-[#D9541E]/15 text-[#D9541E]',
            icon: 'warning',
            progressBg: 'bg-[#D9541E]'
        },
        info: {
            border: 'border-[#D9541E]/40',
            iconBg: 'bg-[#D9541E]/15 text-[#D9541E]',
            icon: 'info',
            progressBg: 'bg-[#D9541E]'
        }
    };
    const cfg = typeConfig[type] || typeConfig.info;

    const toast = document.createElement('div');
    toast.className = `toast-card pointer-events-auto relative overflow-hidden rounded-2xl bg-surface-container-lowest/95 backdrop-blur-xl border p-3.5 sm:p-4 shadow-xl shadow-black/10 transition-all duration-300 ease-out flex items-start gap-3 ${cfg.border}`;
    toast.setAttribute('data-toast', '');
    toast.setAttribute('data-duration', duration.toString());
    toast.setAttribute('role', 'alert');

    toast.innerHTML = `
        <div class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${cfg.iconBg}">
            <span class="material-symbols-outlined text-[20px]">${cfg.icon}</span>
        </div>
        <div class="flex-1 pt-0.5 min-w-0">
            <p class="text-xs sm:text-[13px] font-bold text-[#111111] leading-snug break-words">
                ${message}
            </p>
        </div>
        <button type="button" 
                onclick="event.preventDefault(); event.stopPropagation(); dismissToast(this.closest('[data-toast]'))" 
                class="w-7 h-7 -mr-1 -mt-0.5 rounded-full flex items-center justify-center text-slate-500 hover:text-black hover:bg-black/5 active:scale-90 transition-all shrink-0 cursor-pointer"
                aria-label="Dismiss notification">
            <span class="material-symbols-outlined text-[17px]">close</span>
        </button>
        <div class="toast-progress-bar absolute bottom-0 left-0 h-1 ${cfg.progressBg}" style="width: 100%;"></div>
    `;

    container.appendChild(toast);
    setupToastElement(toast);
};
