/**
 * Rentora Global JS
 */

document.addEventListener('DOMContentLoaded', () => {

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
    // Requires a globally defined CSRF token or fetched from cookie
    const csrftoken = getCookie('csrftoken');
    
    fetch(`/api/wishlist/toggle/${carId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json'
        }
    })
    .then(res => res.json())
    .then(data => {
        const icon = btnElement.querySelector('.material-symbols-outlined');
        if (data.wishlisted) {
            icon.style.fontVariationSettings = "'FILL' 1";
            icon.classList.add('text-red-500');
            icon.classList.remove('text-slate-300', 'hover:text-red-500');
        } else {
            icon.style.fontVariationSettings = "'FILL' 0";
            icon.classList.remove('text-red-500');
            icon.classList.add('text-slate-300', 'hover:text-red-500');
        }
    })
    .catch(err => console.error("Wishlist error:", err));
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
