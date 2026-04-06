document.getElementById('demo-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const form = e.target;
    const status = document.getElementById('form-status');
    const btn = form.querySelector('.btn-submit');
    const consent = document.getElementById('dpdp-consent').checked;

    if (!consent) {
        status.innerHTML = '<p class="status-error">Explicit consent is required under DPDP Act.</p>';
        return;
    }

    // Prepare data
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    // Add Metadata for Consent Log (Critical for DPDP Audits)
    data.consentTimestamp = new Date().toISOString();
    data.sourceUrl = window.location.href;
    data.consentText = "Notice-and-Consent for AI Citation Services";

    btn.disabled = true;
    btn.innerText = "SENDING...";

    try {
        // Replace with your actual API endpoint or Formspree URL
        const response = await fetch('https://formspree.io/f/your-id', {
            method: 'POST',
            body: JSON.stringify(data),
            headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }
        });

        if (response.ok) {
            status.innerHTML = '<p class="status-success">✓ Request received. Our strategist will contact you via WhatsApp/Email within 24 hours.</p>';
            form.reset();
            btn.innerText = "REQUEST SENT";
        } else {
            throw new Error('Submission failed');
        }
    } catch (err) {
        status.innerHTML = '<p class="status-error">Submission error. Please try again or contact support@geo-score.in.</p>';
        btn.disabled = false;
        btn.innerText = "RETRY REQUEST";
    }
});
