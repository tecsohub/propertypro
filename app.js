const map = L.map('map').setView(
  [22.25, 72.2],
  16
);

L.tileLayer(
  'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  {
    maxZoom: 22
  }
).addTo(map);

// --- --- ---

const imageBounds = [
  [22.2446, 72.1933], // southwest
  [22.2525, 72.2060]  // northeast
];

const overlay = L.imageOverlay(
  'assets/layout.png',
  imageBounds,
  {
    opacity: 0.7
  }
);

overlay.addTo(map);

L.rectangle(imageBounds, {
  color: 'red',
  weight: 1
}).addTo(map);

document
  .getElementById('opacity')
  .addEventListener('input', e => {
    overlay.setOpacity(e.target.value);
  });