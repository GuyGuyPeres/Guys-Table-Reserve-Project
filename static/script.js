const grid = document.getElementById('restaurant-grid');
const modal = document.getElementById('modal');
const bookingForm = document.getElementById('booking-form');

let restaurantsData = [];

async function loadRestaurants() {
    const res = await fetch('/api/restaurants');
    restaurantsData = await res.json();
    grid.innerHTML = restaurantsData.map(r => `
        <div class="card">
            <img src="${r.image_url}" alt="${r.name.replace(/'/g, "&#39;")}">
            <h3>${r.name}</h3>
            <p>${r.description}</p>
            <button class="btn" onclick="openBooking('${r.id}')">View Slots</button>
        </div>
    `).join('');
}

function openBooking(id) {
    const restaurant = restaurantsData.find(r => r.id === id);
    if (!restaurant) return;

    document.getElementById('modal-title').innerText = `Book at ${restaurant.name}`;
    document.getElementById('selected-restaurant-id').value = id;

    const container = document.getElementById('slots-container');
    container.innerHTML = restaurant.available_slots.length
        ? restaurant.available_slots.map(s => `
            <span class="slot-pill" onclick="selectSlot('${s}')">${s}</span>
          `).join('')
        : "No slots available today.";

    bookingForm.classList.add('hidden');
    modal.classList.remove('hidden');
}

function selectSlot(time) {
    document.getElementById('selected-time').value = time;
    bookingForm.classList.remove('hidden');
}

bookingForm.onsubmit = async (e) => {
    e.preventDefault();
    const payload = {
        restaurant_id: document.getElementById('selected-restaurant-id').value,
        time_slot: document.getElementById('selected-time').value,
        customer_name: document.getElementById('cust-name').value,
        customer_phone: document.getElementById('cust-phone').value
    };

    const res = await fetch('/api/book', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        alert("Booking Confirmed!");
        location.reload();
    } else {
        const err = await res.json();
        alert(err.detail);
    }
};

function closeModal() { modal.classList.add('hidden'); }
loadRestaurants();