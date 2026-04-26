const grid = document.getElementById('restaurant-grid');
const modal = document.getElementById('modal');
const bookingForm = document.getElementById('booking-form');

let restaurantsData = [];
let selectedSlot = null;

// ── TOAST ──
function showToast(msg, type = 'success') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${type === 'success' ? '✓' : '✕'}</span>
    <span class="toast-msg">${msg}</span>
  `;
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('hiding');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ── LOAD RESTAURANTS ──
async function loadRestaurants() {
  const res = await fetch('/api/restaurants');
  restaurantsData = await res.json();

  if (!restaurantsData.length) {
    grid.innerHTML = `<p style="color:var(--text-muted);text-align:center;grid-column:1/-1;padding:3rem;">No restaurants available yet.</p>`;
    return;
  }

  grid.innerHTML = restaurantsData.map(r => `
    <div class="card" onclick="openBooking('${r.id}')">
      <img src="${r.image_url}" alt="${r.name.replace(/'/g, "&#39;")}">
      <div class="card-overlay"></div>
      <div class="card-content">
        <p class="card-tag">Fine Dining</p>
        <h3>${r.name}</h3>
        <p>${r.description}</p>
        <button class="btn-card">Reserve a Table →</button>
      </div>
    </div>
  `).join('');
}

// ── OPEN BOOKING MODAL ──
function openBooking(id) {
  const restaurant = restaurantsData.find(r => r.id === id);
  if (!restaurant) return;

  selectedSlot = null;
  document.getElementById('modal-title').innerText = restaurant.name;
  document.getElementById('selected-restaurant-id').value = id;

  // Reset all steps
  const dateInput = document.getElementById('booking-date');
  dateInput.value = '';
  // Set min date to today
  dateInput.min = new Date().toISOString().split('T')[0];
  // Set max date to 3 months from now
  const maxDate = new Date();
  maxDate.setMonth(maxDate.getMonth() + 3);
  dateInput.max = maxDate.toISOString().split('T')[0];

  document.getElementById('step-date').classList.remove('hidden');
  document.getElementById('step-time').classList.add('hidden');
  document.getElementById('slots-container').innerHTML = '';
  bookingForm.classList.add('hidden');
  document.getElementById('cust-name').value = '';
  document.getElementById('cust-phone').value = '';

  modal.classList.add('visible');
  document.body.style.overflow = 'hidden';
}

// ── DATE SELECTED ──
function onDateSelected() {
  const date = document.getElementById('booking-date').value;
  if (!date) return;

  const restaurantId = document.getElementById('selected-restaurant-id').value;
  const restaurant = restaurantsData.find(r => r.id === restaurantId);
  if (!restaurant) return;

  // Show time slots
  document.getElementById('step-time').classList.remove('hidden');
  bookingForm.classList.add('hidden');
  selectedSlot = null;

  const container = document.getElementById('slots-container');
  if (restaurant.available_slots.length) {
    container.innerHTML = restaurant.available_slots.map(s => `
      <span class="slot-pill" onclick="selectSlot('${s}', this)">${s}</span>
    `).join('');
  } else {
    container.innerHTML = `<p style="color:var(--text-muted);font-size:0.85rem;">No slots available at this time.</p>`;
  }
}

// ── SELECT SLOT ──
function selectSlot(time, el) {
  document.querySelectorAll('.slot-pill').forEach(p => p.classList.remove('selected'));
  el.classList.add('selected');
  selectedSlot = time;
  document.getElementById('selected-time').value = time;
  bookingForm.classList.remove('hidden');
}

// ── CLOSE MODAL ──
function closeModal() {
  modal.classList.remove('visible');
  document.body.style.overflow = '';
}

modal.addEventListener('click', e => {
  if (e.target === modal) closeModal();
});

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
});

// ── SUBMIT BOOKING ──
bookingForm.onsubmit = async (e) => {
  e.preventDefault();

  const bookingDate = document.getElementById('booking-date').value;
  if (!bookingDate) {
    showToast('Please select a date.', 'error');
    return;
  }

  const payload = {
    restaurant_id: document.getElementById('selected-restaurant-id').value,
    time_slot: document.getElementById('selected-time').value,
    booking_date: bookingDate,
    customer_name: document.getElementById('cust-name').value,
    customer_phone: document.getElementById('cust-phone').value
  };

  const res = await fetch('/api/book', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (res.ok) {
    closeModal();
    showToast('Your reservation has been confirmed!');
    setTimeout(() => loadRestaurants(), 500);
  } else {
    const err = await res.json();
    showToast(err.detail || 'Something went wrong.', 'error');
  }
};

loadRestaurants();