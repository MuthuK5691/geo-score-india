/**
 * GEOSCORE INDIA - Core Site Logic (April 2026)
 * Handles: Razorpay Integration, Performance-Optimized Typewriter, 
 * Intersection Observers, and DPDP Consent Logic.
 */

const PRICING_CONFIG = {
    basePrice: 8499,
    gst: 0.18,
    currency: 'INR'
};

document.addEventListener('DOMContentLoaded', () => {
    initRazorpay();
    initTypewriter();
    initSmoothScroll();
});

/**
 * 1. RAZORPAY PAYMENT INTEGRATION
 * Redirects to /success.html upon verified transaction.
 */
function initRazorpay() {
    const btn = document.getElementById('checkout-btn');
    if (!btn) return;

    btn.onclick = (e) => {
        e.preventDefault();
        
        // Calculate final amount including GST (in paise for Razorpay)
        const finalAmt = PRICING_CONFIG.basePrice * (1 + PRICING_CONFIG.gst);
        const amountInPaise = (finalAmt * 100).toFixed(0);

        const options = {
            "key": "YOUR_RAZORPAY_KEY", // Replace with actual key
            "amount": amountInPaise,
            "currency": PRICING_CONFIG.currency,
            "name": "GeoScore India",
            "description": "Enterprise AI Citation Plan",
            "image": "/assets/logo.png",
            "prefill": {
                "method": "upi"
            },
            "handler": function (response) {
                // Success: Redirect to premium success page
                window.location.href = `/success.html?payment_id=${response.razorpay_payment_id}`;
            },
            "modal": {
                "ondismiss": function() {
                    console.log('Payment window closed by user.');
                }
            },
            "theme": {
                "color": "#D4AF37" // Matches Gold Accent
            }
        };

        const rzp = new Razorpay(options);
        rzp.open();
    };
}

/**
 * 2. PERFORMANCE-OPTIMIZED TYPEWRITER
 * Uses IntersectionObserver to only run when the user is looking at the hero.
 */
function initTypewriter() {
    const target = document.querySelector('#hero-title');
    if (!target) return;

    const textToType = target.innerText;
    target.innerText = ''; // Clear for animation

    const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
            typeEffect(target, textToType);
            observer.disconnect(); // Run once
        }
    }, { threshold: 0.5 });

    observer.observe(target);
}

function typeEffect(element, text, speed = 60) {
    let i = 0;
    function type() {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    type();
}

/**
 * 3. SMOOTH NAVIGATION
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
}

/**
 * 4. DPDP CONSENT VALIDATION (For Demo Form)
 */
const demoForm = document.getElementById('demo-form');
if (demoForm) {
    demoForm.addEventListener('submit', function(e) {
        const consentCheckbox = document.getElementById('dpdp-consent');
        if (consentCheckbox && !consentCheckbox.checked) {
            e.preventDefault();
            alert("DPDP Compliance: You must provide consent to process your business data.");
        }
    });
}
