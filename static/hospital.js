let map = L.map('map').setView([20.5937, 78.9629], 5);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

let markers = [];

// =========================
// CLEAR OLD MARKERS
// =========================
function clearMarkers() {
    markers.forEach(marker => {
        map.removeLayer(marker);
    });

    markers = [];
}

// =========================
// SEARCH HOSPITALS
// =========================
function renderHospitals(hospitals){

    const list =
    document.getElementById('resultsList');

    const count =
    document.getElementById('resultsCount');

    if(!hospitals.length){

        list.innerHTML = `
        <div class="empty">
            <div style="font-size:70px;">😕</div>
            <h3>No Hospitals Found</h3>
            <p>Try another location.</p>
        </div>
        `;

        count.innerHTML = '0 Found';

        return;
    }

    count.innerHTML = `${hospitals.length} Found`;

    list.innerHTML = '';

    hospitals.forEach((hospital,index)=>{

        const name =
        hospital.tags?.name ||
        "Unnamed Hospital";

        const address =
        hospital.tags?.["addr:full"] ||
        hospital.tags?.["addr:street"] ||
        hospital.tags?.["addr:city"] ||
        "Address unavailable";

        const phone =
        hospital.tags?.phone ||
        hospital.tags?.contact ||
        "+91 XXXXX XXXXX";

        const lat = hospital.lat;
        const lon = hospital.lon;

        const rating =
        (4 + Math.random()).toFixed(1);

        const marker =
        createMarker(lat, lon, name);

        const card =
        document.createElement('div');

        card.className = 'hospital-card';

        card.innerHTML = `

        <div class="top-strip"></div>

        <div class="card-title">
            ${name}
        </div>

        <div class="badges">

            <div class="badge badge-hospital">
                Hospital
            </div>

            <div class="badge badge-open">
                Open Now
            </div>

        </div>

        <div class="address">
            📍 ${address}
        </div>

        <div class="meta">
            <span>📞 ${phone}</span>
        </div>

        <div class="rating">
            ⭐ ${rating}
        </div>

        <div class="card-actions">

            <a
            href="tel:${phone}"
            class="call-btn"
            >
            Call
            </a>

            <a
            href="https://www.google.com/maps/dir/?api=1&destination=${lat},${lon}"
            target="_blank"
            class="direction-btn"
            >
            Directions
            </a>

        </div>
        `;

        card.addEventListener('click',()=>{

            map.setView([lat,lon],16);

            marker.openPopup();

            document
            .querySelectorAll('.hospital-card')
            .forEach(c=>c.classList.remove('selected'));

            card.classList.add('selected');

        });

        list.appendChild(card);

    });

}
// =========================
// USE MY LOCATION
// =========================
function useMyLocation() {

    navigator.geolocation.getCurrentPosition(async (position) => {

        const lat = position.coords.latitude;
        const lng = position.coords.longitude;

        try {

            const response = await fetch("/nearby_hospitals", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    lat: lat,
                    lng: lng
                })
            });

            const data = await response.json();

            clearMarkers();

            map.setView([lat, lng], 13);

            const resultsDiv =
                document.getElementById("resultsList");

            resultsDiv.innerHTML = "";

            document.getElementById("resultsCount").innerText =
                `${data.hospitals.length} found`;

            data.hospitals.forEach(hospital => {

                const marker = L.marker([
                    hospital.lat,
                    hospital.lng
                ]).addTo(map);

                marker.bindPopup(`
                    <b>${hospital.name}</b><br>
                    ${hospital.address}
                `);

                markers.push(marker);

                resultsDiv.innerHTML += `

                <div class="hospital-card">

                    <div class="hospital-top">

                        <div>
                            <h3>${hospital.name}</h3>

                            <p class="hospital-address">
                                ${hospital.address}
                            </p>
                        </div>

                        <span class="${
                            hospital.open_now
                            ? 'open-badge'
                            : 'closed-badge'
                        }">

                            ${
                                hospital.open_now
                                ? 'Open Now'
                                : 'Closed'
                            }

                        </span>

                    </div>

                    <div class="hospital-meta">
                        ⭐ ${hospital.rating || 'N/A'}
                    </div>

                    <div class="hospital-actions">

                        <a
                            href="https://www.google.com/maps?q=${hospital.lat},${hospital.lng}"
                            target="_blank"
                            class="direction-btn"
                        >
                            Directions
                        </a>

                    </div>

                </div>
                `;
            });

        } catch (error) {

            console.log(error);

            alert("Error fetching nearby hospitals");
        }

    });

}

// =========================
// ENTER KEY SEARCH
// =========================
document.getElementById("searchInput")
.addEventListener("keypress", function(e) {

    if (e.key === "Enter") {
        searchHospitals();
    }

});
