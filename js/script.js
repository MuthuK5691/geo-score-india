const CONFIG = {
    price: 8499,
    gst: 1.18,
    rzpKey: "YOUR_RAZORPAY_KEY" // REPLACE WITH ACTUAL KEY
};

document.addEventListener('DOMContentLoaded', () => {
    // 1. PERFORMANCE-FIRST TYPEWRITER
    const heroTitle = document.getElementById('hero-title');
    if (heroTitle) {
        const text = heroTitle.innerText;
        heroTitle.innerText = '';
        
        const observer = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                let i = 0;
                const type = () => {
                    if (i < text.length) {
                        heroTitle.innerHTML += text.charAt(i++);
                        setTimeout(type, 50);
                    }
                };
                type();
                observer.disconnect();
            }
        }, { threshold: 0.5 });
        observer.observe(heroTitle);
    }

    // 2. RAZORPAY 2026 SECURE FLOW
    const payBtn = document.getElementById('checkout-btn');
    if (payBtn) {
        payBtn.onclick = () => {
            const amount = (CONFIG.price * CONFIG.gst * 100).toFixed(0);
            const options = {
                "key": CONFIG.rzpKey,
                "amount": amount,
                "currency": "INR",
                "name": "GeoScore India",
                "description": "Enterprise AI Citation Plan",
                "handler": (res) => { 
                    window.location.href = "/success.html?ref=" + res.razorpay_payment_id; 
                },
                "theme": { "color": "#D4AF37" }
            };
            new Razorpay(options).open();
        };
    }

    // 3. DPDP-COMPLIANT FORM HANDLER
    const form = document.getElementById('demo-form');
    if (form) {
        form.onsubmit = async (e) => {
            e.preventDefault();
            const btn = form.querySelector('.btn-submit');
            const status = document.getElementById('form-status');
            
            btn.disabled = true;
            btn.innerText = "VERIFYING...";

            const data = Object.fromEntries(new FormData(form).entries());
            data.submittedAt = new Date().toISOString(); // DPDP Audit Log

            try {
                const response = await fetch('https://formspree.io/f/your-id', { // REPLACE WITH YOUR ID
                    method: 'POST',
                    body: JSON.stringify(data),
                    headers: { 'Content-Type': 'application/json' }
                });
                if (response.ok) {
                    status.innerHTML = "<p style='color:#25D366; font-weight:bold;'>✓ Audit Requested. Check WhatsApp in 24h.</p>";
                    form.reset();
                } else { throw new Error(); }
            } catch {
                status.innerHTML = "<p style='color:#ff4444'>System Error. Contact Chennai HQ.</p>";
                btn.disabled = false;
            } finally {
                btn.innerText = "RUN AI AUDIT";
            }
        };
    }
});
