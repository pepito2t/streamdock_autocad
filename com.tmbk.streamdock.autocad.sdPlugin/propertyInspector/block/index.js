const MANUAL_OPTION = '';
const $local = false, $back = false,
  $dom = {
    main: $('.sdpi-wrapper'),
    blockSelect: $('#block-select'),
    refreshBlocks: $('#refresh-blocks'),
    block: $('#block'),
    fixed: $('#fixed'),
    scale: $('#scale'),
    rotation: $('#rotation'),
  },
  $propEvent = {
    didReceiveSettings() {
      $dom.block.value = $settings.block || '';
      $dom.fixed.checked = $settings.fixed !== false;
      $dom.scale.value = $settings.scale ?? '';
      $dom.rotation.value = $settings.rotation ?? '';
      syncSelect();
      renderFixed();
    },
    sendToPropertyInspector(data) {
      if (data.event === 'blocks') {
        renderBlocks(data.blocks);
        return;
      }
      handleNotice(data);
    },
  };

function renderBlocks(blocks) {
  $dom.blockSelect.innerHTML = '';
  const manual = document.createElement('option');
  manual.value = MANUAL_OPTION;
  manual.textContent = blocks.length ? '— choisir —' : 'AutoCAD fermé : saisir le nom';
  $dom.blockSelect.appendChild(manual);
  blocks.forEach(name => {
    const option = document.createElement('option');
    option.value = name;
    option.textContent = name;
    $dom.blockSelect.appendChild(option);
  });
  syncSelect();
}

function syncSelect() {
  const wanted = $dom.block.value.toLowerCase();
  const match = Array.from($dom.blockSelect.options).find(option => option.value.toLowerCase() === wanted);
  $dom.blockSelect.value = match ? match.value : MANUAL_OPTION;
}

function renderFixed() {
  const display = $dom.fixed.checked ? 'flex' : 'none';
  $dom.scale.parentElement.style.display = display;
  $dom.rotation.parentElement.style.display = display;
}

$dom.blockSelect.on('change', () => {
  if ($dom.blockSelect.value === MANUAL_OPTION) return;
  $dom.block.value = $dom.blockSelect.value;
  $settings.block = $dom.blockSelect.value;
});
$dom.refreshBlocks.on('click', () => $websocket.sendToPlugin({ command: 'blocks' }));
$dom.block.on('input', () => { $settings.block = $dom.block.value; syncSelect(); });
$dom.fixed.on('change', () => { $settings.fixed = $dom.fixed.checked; renderFixed(); });
$dom.scale.on('input', () => { $settings.scale = $dom.scale.value; });
$dom.rotation.on('input', () => { $settings.rotation = $dom.rotation.value; });
