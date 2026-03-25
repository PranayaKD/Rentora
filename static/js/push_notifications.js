// Push Notification Subscription Logic
const urlB64ToUint8Array = base64String => {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
};

async function subscribeUser() {
    if ('serviceWorker' in navigator) {
        try {
            const registration = await navigator.serviceWorker.ready;
            
            // Re-use existing VAPID_PUBLIC_KEY from window object
            const vapidPublicKey = window.VAPID_PUBLIC_KEY;
            if (!vapidPublicKey) {
                console.error('VAPID Public Key not found.');
                return;
            }

            const applicationServerKey = urlB64ToUint8Array(vapidPublicKey);
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: applicationServerKey
            });

            console.log('User is subscribed:', subscription);
            
            // Send subscription to server
            await fetch('/api/push/subscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(subscription)
            });

        } catch (err) {
            console.log('Failed to subscribe the user: ', err);
        }
    }
}

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

// Request permission on load or on interaction
if ('Notification' in window) {
    if (Notification.permission === 'default') {
        // We might want to wait for interaction before asking, but for now:
        // Notification.requestPermission().then(permission => {
        //     if (permission === 'granted') {
        //         subscribeUser();
        //     }
        // });
    } else if (Notification.permission === 'granted') {
        subscribeUser();
    }
}
