const CONFIG = {
    basePrice: 8499,
    currency: 'INR',
    gstRate: 0.18
};

// Initialize only when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    handleTypewriter();
    setupRazorpay();
});

// Fix: Lazy load typewriter only when visible
function handleTypewriter() {
    const el = document.querySelector('#hero-title');
    const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
            // Start animation logic here
            observer.disconnect();
        }
    });
    observer.observe(el);
}

// Fix: Professional Payment Flow (No Alerts)
function setupRazorpay() {
    const btn = document.getElementById('rzp-button');
    if (!btn) return;

    btn.onclick = (e) => {
        e.preventDefault();
        
        const totalWithGST = CONFIG.basePrice * (1 + CONFIG.gstRate);
        
        const options = {
            "key": "YOUR_RAZORPAY_KEY", 
            "amount": (totalWithGST * 100).toFixed(0), // In paise
            "currency": CONFIG.currency,
            "name": "GeoScore India",
            "description": "Professional Plan Subscription",
            "prefill": { "method": "upi" },
            "handler": function (response) {
                window.location.href = "/success?id=" + response.razorpay_payment_id;
            },
            "theme": { "color": "#D4AF37" }
        };

        try {
            const rzp = new Razorpay(options);
            rzp.open();
        } catch (err) {
            console.error("Payment Error:", err);
            btn.innerText = "Payment Service Offline";
        }
    };
}
