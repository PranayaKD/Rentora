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

});

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
