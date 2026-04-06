const CONFIG = {
    basePrice: 8499,
    gstRate: 0.18,
    currency: 'INR'
};

document.addEventListener('DOMContentLoaded', () => {
    initTypewriter();
    initCheckout();
});

/**
 * Lazy-load typewriter only when in view
 */
function initTypewriter() {
    const target = document.getElementById('typewriter');
    if (!target) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                startTypewriterEffect(target);
                observer.unobserve(target);
            }
        });
    }, { threshold: 0.5 });

    observer.observe(target);
}

/**
 * Handle Razorpay Checkout with proper error handling
 */
function initCheckout() {
    const checkoutBtn = document.getElementById('checkout-button');
    if (!checkoutBtn) return;

    checkoutBtn.addEventListener('click', () => {
        const totalAmount = CONFIG.basePrice * (1 + CONFIG.gstRate);
        
        const options = {
            "key": "YOUR_RAZORPAY_KEY", 
            "amount": (totalAmount * 100).toString(), // Razorpay expects paise
            "currency": CONFIG.currency,
            "name": "GeoScore",
            "description": "Professional Plan Subscription",
            "handler": function (response) {
                // Success logic
                console.log("Payment ID:", response.razorpay_payment_id);
                window.location.href = "/success";
            },
            "prefill": {
                "method": "upi" // Defaults to UPI for Indian context
            },
            "theme": {
                "color": "#050505"
            }
        };

        try {
            const rzp1 = new Razorpay(options);
            rzp1.open();
        } catch (error) {
            console.error("Payment failed to initialize:", error);
            // Fallback for user feedback
            checkoutBtn.innerText = "Error - Try Again";
        }
    });
}

/** * Simple debounced GST Calculator (if user changes quantity/input)
 */
let debounceTimer;
function updatePriceUI() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        const display = document.getElementById('display-price');
        const formatted = new Intl.NumberFormat('en-IN').format(CONFIG.basePrice);
        display.innerText = formatted;
    }, 250);
}
