/* ══ DJIB EXCHANGE — Main JS ══ */

// ── Particles background ────────────────────────────────────────
function initParticles() {
  const container = document.querySelector('.particles');
  if (!container) return;
  for (let i = 0; i < 20; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    p.style.cssText = `
      left: ${Math.random() * 100}%;
      width: ${Math.random() * 3 + 1}px;
      height: ${Math.random() * 3 + 1}px;
      animation-duration: ${Math.random() * 15 + 10}s;
      animation-delay: ${Math.random() * 10}s;
      opacity: 0;
    `;
    container.appendChild(p);
  }
}

// ── File upload preview ─────────────────────────────────────────
function initFileUpload() {
  const fileInput = document.querySelector('input[type="file"]');
  if (!fileInput) return;

  const dropZone = document.querySelector('.file-drop-zone');
  const preview = document.querySelector('.file-preview');
  const previewImg = preview ? preview.querySelector('img') : null;
  const labelEl = dropZone ? dropZone.querySelector('.label') : null;

  function handleFile(file) {
    if (!file || !file.type.startsWith('image/')) return;
    const reader = new FileReader();
    reader.onload = e => {
      if (previewImg) previewImg.src = e.target.result;
      if (preview) preview.style.display = 'block';
      if (labelEl) labelEl.innerHTML = `<strong>${file.name}</strong>`;
    };
    reader.readAsDataURL(file);
  }

  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) handleFile(fileInput.files[0]);
  });

  if (dropZone) {
    dropZone.addEventListener('dragover', e => {
      e.preventDefault();
      dropZone.classList.add('drag-over');
    });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
    dropZone.addEventListener('drop', e => {
      e.preventDefault();
      dropZone.classList.remove('drag-over');
      const file = e.dataTransfer.files[0];
      if (file) {
        const dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;
        handleFile(file);
      }
    });
  }
}

// ── Live amount converter ───────────────────────────────────────
function initAmountConverter() {
  const amountInput = document.getElementById('id_amount_sent');
  const receiveDisplay = document.getElementById('receive-amount');
  const rate = parseFloat(document.body.dataset.rate || '1.005639');

  if (!amountInput || !receiveDisplay) return;

  amountInput.addEventListener('input', () => {
    const val = parseFloat(amountInput.value);
    if (!isNaN(val) && val > 0) {
      receiveDisplay.textContent = (val * rate).toFixed(4) + ' USD';
    } else {
      receiveDisplay.textContent = '— USD';
    }
  });
}

// ── Copy to clipboard ───────────────────────────────────────────
function initCopyBtns() {
  document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const text = btn.dataset.copy;
      navigator.clipboard.writeText(text).then(() => {
        const orig = btn.textContent;
        btn.textContent = 'Copied!';
        btn.style.background = 'rgba(16,185,129,0.2)';
        btn.style.color = '#10b981';
        setTimeout(() => {
          btn.textContent = orig;
          btn.style.background = '';
          btn.style.color = '';
        }, 1800);
      }).catch(() => {
        // fallback
        const ta = document.createElement('textarea');
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        btn.textContent = 'Copied!';
        setTimeout(() => btn.textContent = orig, 1800);
      });
    });
  });
}

// ── Lightbox ────────────────────────────────────────────────────
function initLightbox() {
  const lightbox = document.getElementById('lightbox');
  if (!lightbox) return;
  const img = lightbox.querySelector('img');
  const close = lightbox.querySelector('.lightbox-close');

  document.querySelectorAll('[data-lightbox]').forEach(el => {
    el.style.cursor = 'zoom-in';
    el.addEventListener('click', () => {
      img.src = el.dataset.lightbox || el.querySelector('img')?.src || el.src;
      lightbox.classList.add('active');
    });
  });
  close.addEventListener('click', () => lightbox.classList.remove('active'));
  lightbox.addEventListener('click', e => {
    if (e.target === lightbox) lightbox.classList.remove('active');
  });
}

// ── Dashboard quick status update ──────────────────────────────
function initStatusButtons() {
  document.querySelectorAll('[data-status-btn]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const pk = btn.dataset.pk;
      const status = btn.dataset.status;
      const row = btn.closest('tr');

      try {
        const resp = await fetch(`/dashboard/requests/${pk}/status/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
          },
          body: JSON.stringify({ status }),
        });
        const data = await resp.json();
        if (data.success && row) {
          const badgeCell = row.querySelector('.badge');
          if (badgeCell) {
            const map = {
              pending: 'badge-pending',
              processing: 'badge-processing',
              completed: 'badge-completed',
              rejected: 'badge-rejected',
            };
            badgeCell.className = `badge ${map[status]}`;
            badgeCell.innerHTML = `${data.status}`;
          }
        }
      } catch (e) {
        console.error(e);
      }
    });
  });
}

// ── CSRF helper ─────────────────────────────────────────────────
function getCookie(name) {
  let value = null;
  document.cookie.split(';').forEach(c => {
    const [k, v] = c.trim().split('=');
    if (k === name) value = decodeURIComponent(v);
  });
  return value;
}

// ── Dismiss alerts ──────────────────────────────────────────────
function initAlerts() {
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.4s';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 400);
    }, 5000);
  });
}

// ── Init ────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initParticles();
  initFileUpload();
  initAmountConverter();
  initCopyBtns();
  initLightbox();
  initStatusButtons();
  initAlerts();
});
