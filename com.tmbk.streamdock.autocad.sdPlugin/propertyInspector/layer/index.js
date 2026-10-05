const MANUAL_OPTION = '';
const $local = false, $back = false,
  $dom = {
    main: $('.sdpi-wrapper'),
    layerSelect: $('#layer-select'),
    refreshLayers: $('#refresh-layers'),
    layer: $('#layer'),
    create: $('#create'),
  },
  $propEvent = {
    didReceiveSettings() {
      $dom.layer.value = $settings.layer || '';
      $dom.create.checked = $settings.create !== false;
      syncSelect();
    },
    sendToPropertyInspector(data) {
      if (data.event === 'layers') {
        renderLayers(data.layers, data.current);
        return;
      }
      handleNotice(data);
    },
  };

function renderLayers(layers, current) {
  $dom.layerSelect.innerHTML = '';
  const manual = document.createElement('option');
  manual.value = MANUAL_OPTION;
  manual.textContent = layers.length ? '— choisir —' : 'AutoCAD fermé : saisir le nom';
  $dom.layerSelect.appendChild(manual);
  layers.forEach(name => {
    const option = document.createElement('option');
    option.value = name;
    option.textContent = name === current ? `${name} (courant)` : name;
    $dom.layerSelect.appendChild(option);
  });
  syncSelect();
}

function syncSelect() {
  const wanted = $dom.layer.value.toLowerCase();
  const match = Array.from($dom.layerSelect.options).find(option => option.value.toLowerCase() === wanted);
  $dom.layerSelect.value = match ? match.value : MANUAL_OPTION;
}

$dom.layerSelect.on('change', () => {
  if ($dom.layerSelect.value === MANUAL_OPTION) return;
  $dom.layer.value = $dom.layerSelect.value;
  $settings.layer = $dom.layerSelect.value;
});
$dom.refreshLayers.on('click', () => $websocket.sendToPlugin({ command: 'layers' }));
$dom.layer.on('input', () => { $settings.layer = $dom.layer.value; syncSelect(); });
$dom.create.on('change', () => { $settings.create = $dom.create.checked; });
