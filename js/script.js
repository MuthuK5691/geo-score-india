const PRICING_CONFIG = { basePrice: 8499, gst: 0.18 };

document.addEventListener('DOMContentLoaded', () => {
    initTypewriter();
    initRazorpay();
    initDemoForm();
});

function initTypewriter() {
    const target = document.querySelector('#hero-title');
    if (!target) return;
    const text = target.innerText;
    target.innerText = '';
    let i = 0;
    function type() {
        if (i < text.length) {
            target.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, 70);
        }
    }
    type();
}

function initRazorpay() {
    const btn = document.getElementById('checkout-btn');
    if (!btn) return;
    btn.onclick = () => {
        const amount = (PRICING_CONFIG.basePrice * 1.18 * 100).toFixed(0);
        const options = {
            "key": "YOUR_RAZORPAY_KEY",
            "amount": amount,
            "currency": "INR",
            "name": "GeoScore India",
            "handler": (res) => { window.location.href = "/success.html?id=" + res.razorpay_payment_id; },
            "theme": { "color": "#D4AF37" }
        };
        new Razorpay(options).open();
    };
}

function initDemoForm() {
    const form = document.getElementById('demo-form');
    if (!form) return;
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const status = document.getElementById('form-status');
        const btn = form.querySelector('.btn-submit');
        
        btn.disabled = true;
        btn.innerText = "SENDING...";

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch('https://formspree.io/f/your-id', {
                method: 'POST',
                body: JSON.stringify(data),
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }
            });
            if (response.ok) {
                status.innerHTML = '<p style="color:#25D366">✓ Audit Request Received.</p>';
                form.reset();
            } else { throw new Error(); }
        } catch {
            status.innerHTML = '<p style="color:#ff4444">Error. Contact support@geo-score.in</p>';
        } finally {
            btn.disabled = false;
            btn.innerText = "RUN AI AUDIT";
        }
    });
}
