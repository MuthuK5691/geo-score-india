const CONFIG = {
    price: 8499,
    gst: 1.18, // 18% GST
    rzpKey: "YOUR_RAZORPAY_KEY" // REPLACE THIS
};

document.addEventListener('DOMContentLoaded', () => {
    // 1. Typewriter Animation
    const heroTitle = document.getElementById('hero-title');
    const text = heroTitle.innerText;
    heroTitle.innerText = '';
    let i = 0;
    const type = () => {
        if (i < text.length) {
            heroTitle.innerHTML += text.charAt(i++);
            setTimeout(type, 60);
        }
    };
    type();

    // 2. Razorpay Logic
    const payBtn = document.getElementById('checkout-btn');
    if (payBtn) {
        payBtn.onclick = () => {
            const options = {
                "key": CONFIG.rzpKey,
                "amount": (CONFIG.price * CONFIG.gst * 100).toFixed(0),
                "currency": "INR",
                "name": "GeoScore India",
                "description": "Enterprise AI Citation Plan",
                "handler": (res) => { window.location.href = "/success.html?pay_id=" + res.razorpay_payment_id; },
                "theme": { "color": "#D4AF37" }
            };
            const rzp = new Razorpay(options);
            rzp.open();
        };
    }

    // 3. Form Logic
    const form = document.getElementById('demo-form');
    if (form) {
        form.onsubmit = async (e) => {
            e.preventDefault();
            const btn = form.querySelector('.btn-submit');
            const status = document.getElementById('form-status');
            
            btn.disabled = true;
            btn.innerText = "SENDING...";

            const data = Object.fromEntries(new FormData(form).entries());
            
            try {
                const response = await fetch('https://formspree.io/f/your-id', {
                    method: 'POST',
                    body: JSON.stringify(data),
                    headers: { 'Content-Type': 'application/json' }
                });
                if (response.ok) {
                    status.innerHTML = "<p style='color:#25D366'>✓ Audit Request Sent Successfully.</p>";
                    form.reset();
                } else { throw new Error(); }
            } catch {
                status.innerHTML = "<p style='color:#ff4444'>Submission Error. Try again.</p>";
                btn.disabled = false;
            } finally {
                btn.innerText = "RUN AI AUDIT";
            }
        };
    }
});
