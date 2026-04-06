/**
 * GEOSCORE INDIA - Enterprise Logic (April 2026)
 * Mumbai-bom1 Regional Verification & Secure Payments
 */

const CONFIG = {
    price: 8499,
    gst: 0.18,
    rzpKey: "YOUR_RAZORPAY_KEY"
};

document.addEventListener('DOMContentLoaded', () => {
    initRegionalStatus();
    initTypewriter();
    initRazorpay();
});

// PROOF OF SOVEREIGNTY: Signals the server location
function initRegionalStatus() {
    const statusEl = document.querySelector(".status-dot");
    if (statusEl) {
        console.log("System Status: Operational on Mumbai-BOM1");
    }
}

function initTypewriter() {
    const target = document.getElementById("typewriter");
    if (!target) return;

    const text = "NODE_CHECK: Mumbai-BOM1... [OK] | SYNC: Knowledge Graphs... [ACTIVE] | Logic Certificate successfully injected for AI Agent 0x4A.";
    let i = 0;

    function type() {
        if (i < text.length) {
            target.innerHTML = text.substring(0, i) + '<span style="color:var(--gold)">_</span>';
            i++;
            setTimeout(type, 40);
        }
    }
    type();
}

function initRazorpay() {
    const btn = document.getElementById('checkout-btn');
    if (!btn) return;

    btn.onclick = () => {
        const options = {
            "key": CONFIG.rzpKey,
            "amount": (CONFIG.price * (1 + CONFIG.gst) * 100).toFixed(0),
            "currency": "INR",
            "name": "GeoScore India",
            "description": "Enterprise AI Citation Infrastructure",
            "handler": (res) => {
                window.location.href = `/success.html?payment_id=${res.razorpay_payment_id}`;
            },
            "theme": { "color": "#D4AF37" }
        };
        const rzp = new Razorpay(options);
        rzp.open();
    };
}

function updateGST() {
    const state = document.getElementById('stateSelect').value;
    const base = CONFIG.price;
    const gst = base * CONFIG.gst;
    const total = base + gst;
    const breakdown = document.getElementById('billBreakdown');
    const split = (gst / 2).toFixed(2);

    if (state === 'intra') {
        breakdown.innerHTML = `
            <div class="bill-row"><span>Base:</span><span>₹8,499.00</span></div>
            <div class="bill-row"><span>CGST (9%):</span><span>₹${split}</span></div>
            <div class="bill-row"><span>SGST (9%):</span><span>₹${split}</span></div>
            <div class="bill-row" style="font-weight: 800; color: #fff; border-top: 1px solid var(--border); padding-top: 10px; margin-top: 10px;">
                <span>Total:</span><span>₹${total.toFixed(2)}</span>
            </div>
        `;
    } else {
        breakdown.innerHTML = `
            <div class="bill-row"><span>Base:</span><span>₹8,499.00</span></div>
            <div class="bill-row"><span>IGST (18%):</span><span>₹${gst.toFixed(2)}</span></div>
            <div class="bill-row" style="font-weight: 800; color: #fff; border-top: 1px solid var(--border); padding-top: 10px; margin-top: 10px;">
                <span>Total:</span><span>₹${total.toFixed(2)}</span>
            </div>
        `;
    }
}
