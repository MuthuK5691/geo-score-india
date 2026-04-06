/**
 * GEOSCORE INDIA - Core Site Logic (April 2026)
 * Combined Logic for Payments, Animations, and DPDP Compliance.
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
    initDemoForm(); // Handles the Contact/Demo form submission
});

/**
 * 1. RAZORPAY PAYMENT INTEGRATION
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
 * Runs only when the user scrolls to the hero title.
 */
function initTypewriter() {
    const target = document.querySelector('#hero-title');
    if (!target) return;

    const textToType = target.innerText;
    target.innerText = ''; // Clear for animation

    const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
            let i = 0;
            function type() {
                if (i < textToType.length) {
                    target.innerHTML += textToType.charAt(i);
                    i++;
                    setTimeout(type, 60);
                }
            }
            type();
            observer.disconnect(); // Run once
        }
    }, { threshold: 0.5 });

    observer.observe(target);
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
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

/**
 * 4. DEMO FORM SUBMISSION & DPDP CONSENT
 */
function initDemoForm() {
    const form = document.getElementById('demo-form');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const status = document.getElementById('form-status');
        const btn = form.querySelector('.btn-submit');
        const consentCheckbox = document.getElementById('dpdp-consent');

        // 1. DPDP Compliance Check
        if (consentCheckbox && !consentCheckbox.checked) {
            status.innerHTML = '<p class="status-error">Explicit consent is required under DPDP Act.</p>';
            return;
        }

        // 2. Prepare Data
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Metadata for Consent Logs
        data.consentTimestamp = new Date().toISOString();
        data.sourceUrl = window.location.href;
        data.consentText = "Notice-and-Consent for AI Citation Services";

        // 3. UI Feedback
        btn.disabled = true;
        btn.innerText = "SENDING...";

        try {
            // Replace with your Formspree URL
            const response = await fetch('https://formspree.io/f/your-id', {
                method: 'POST',
                body: JSON.stringify(data),
                headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                status.innerHTML = '<p class="status-success">✓ Request received. We will contact you within 24 hours.</p>';
                form.reset();
                btn.innerText = "REQUEST SENT";
            } else {
                throw new Error('Submission failed');
            }
        } catch (err) {
            status.innerHTML = '<p class="status-error">Submission error. Please try again or contact support.</p>';
            btn.disabled = false;
            btn.innerText = "RETRY REQUEST";
        }
    });
}
