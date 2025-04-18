// map.js
document.addEventListener("DOMContentLoaded", () => {
  const coords = [-2.9057, -41.7754]; // Parnaíba, PI
  const map = L.map('map').setView(coords, 13);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);

  L.marker(coords)
    .addTo(map)
    .bindPopup('Condomínio em Parnaíba')
    .openPopup();

  L.circle(coords, {
    radius: 500,
    color: '#007bff',
    fillOpacity: 0.1
  }).addTo(map);
});
