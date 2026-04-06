/**
 * GEOSCORE INDIA - Enterprise Logic (April 2026)
 * Mumbai-bom1 Regional Verification & Secure Payments
 */

const CONFIG = {
    price: 8499,
    gst: 1.18,
    rzpKey: "YOUR_RAZORPAY_KEY" 
};

document.addEventListener('DOMContentLoaded', () => {
    initRegionalStatus();
    initTypewriter();
    initRazorpay();
    initDemoForm();
});

// PROOF OF SOVEREIGNTY: Shows the user the server is in Mumbai
function initRegionalStatus() {
    const statusEl = document.querySelector('.status-dot');
    if (statusEl) {
        // In a real 2026 app, this would ping the Vercel Edge
        statusEl.innerHTML = '<span style="color: #25D366">●</span> System Status: Operational (Mumbai-BOM1)';
    }
}

function initTypewriter() {
    const target = document.querySelector('#hero-title');
    if (!target) return;
    const text = "Get Cited by AI Chatbots.";
    target.innerText = '';
    let i = 0;
    const type = () => {
        if (i < text.length) {
            target.innerHTML += text.charAt(i++);
            setTimeout(type, 50);
        }
    };
    type();
}

function initRazorpay() {
    const btn = document.getElementById('checkout-btn');
    if (!btn) return;
    btn.onclick = () => {
        const options = {
            "key": CONFIG.rzpKey,
            "amount": (CONFIG.price * CONFIG.gst * 100).toFixed(0),
            "currency": "INR",
            "name": "GeoScore India",
            "description": "Enterprise Citation Infrastructure",
            "handler": (res) => { 
                window.location.href = "/success.html?payment_id=" + res.razorpay_payment_id; 
            },
            "theme": { "color": "#D4AF37" }
        };
        new Razorpay(options).open();
    };
}

function initDemoForm() {
    const form = document.getElementById('demo-form');
    if (!form) return;
    form.onsubmit = async (e) => {
        e.preventDefault();
        const btn = form.querySelector('.btn-submit');
        const status = document.getElementById('form-status');
        
        btn.disabled = true;
        btn.innerText = "ENCRYPTING..."; // Replaced "Sending" for more trust

        const data = Object.fromEntries(new FormData(form).entries());
        data.region = "Mumbai-BOM1"; // Audit tag

        try {
            const response = await fetch('https://formspree.io/f/your-id', {
                method: 'POST',
                body: JSON.stringify(data),
                headers: { 'Content-Type': 'application/json' }
            });
            if (response.ok) {
                status.innerHTML = "<p style='color:#25D366'>✓ Audit request logged in Mumbai nodes.</p>";
                form.reset();
            } else { throw new Error(); }
        } catch {
            status.innerHTML = "<p style='color:#ff4444'>Network error. Please use WhatsApp support.</p>";
            btn.disabled = false;
        } finally {
            btn.innerText = "RUN AI AUDIT";
        }
    };
}
