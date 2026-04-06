const PRICING_CONFIG = {
    basePrice: 8499,
    gst: 0.18,
    currency: 'INR'
};

document.addEventListener('DOMContentLoaded', () => {
    initRazorpay();
    initTypewriterObserver();
});

function initRazorpay() {
    const btn = document.getElementById('checkout-btn');
    if (!btn) return;

    btn.onclick = (e) => {
        const finalAmt = PRICING_CONFIG.basePrice * (1 + PRICING_CONFIG.gst);
        
        const options = {
            "key": "YOUR_RAZORPAY_KEY", 
            "amount": (finalAmt * 100).toFixed(0), // in paise
            "currency": PRICING_CONFIG.currency,
            "name": "GeoScore India",
            "description": "Enterprise AI Citation Plan",
            "prefill": { "method": "upi" },
            "handler": function (response) {
                console.log("Payment Successful:", response.razorpay_payment_id);
                window.location.href = "/thank-you";
            },
            "theme": { "color": "#050505" }
        };
        
        const rzp = new Razorpay(options);
        rzp.open();
    };
}

function initTypewriterObserver() {
    const target = document.querySelector('#hero-title');
    const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
            // Your typewriter animation logic here
            observer.disconnect();
        }
    });
    observer.observe(target);
}
