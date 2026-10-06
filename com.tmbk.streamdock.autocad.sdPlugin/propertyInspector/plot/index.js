const MANUAL_OPTION = '';
const $local = false, $back = false,
  $dom = {
    main: $('.sdpi-wrapper'),
    pageSetupSelect: $('#page-setup-select'),
    refreshPageSetups: $('#refresh-page-setups'),
    pageSetup: $('#page-setup'),
    modeDevice: $('#mode-device'),
    modePdf: $('#mode-pdf'),
    outputFolderItem: $('#output-folder-item'),
    outputFolder: $('#output-folder'),
  },
  $propEvent = {
    didReceiveSettings() {
      $dom.pageSetup.value = $settings.page_setup || '';
      $dom.modePdf.checked = $settings.mode === 'pdf';
      $dom.modeDevice.checked = !$dom.modePdf.checked;
      $dom.outputFolder.value = $settings.output_folder || '';
      syncSelect();
      renderMode();
    },
    sendToPropertyInspector(data) {
      if (data.event === 'page_setups') {
        renderPageSetups(data.page_setups);
        return;
      }
      handleNotice(data);
    },
  };

function renderPageSetups(setups) {
  $dom.pageSetupSelect.innerHTML = '';
  const manual = document.createElement('option');
  manual.value = MANUAL_OPTION;
  manual.textContent = setups.length ? '— choisir —' : 'AutoCAD fermé : saisir le nom';
  $dom.pageSetupSelect.appendChild(manual);
  setups.forEach(name => {
    const option = document.createElement('option');
    option.value = name;
    option.textContent = name;
    $dom.pageSetupSelect.appendChild(option);
  });
  syncSelect();
}

function syncSelect() {
  const wanted = $dom.pageSetup.value.toLowerCase();
  const match = Array.from($dom.pageSetupSelect.options).find(option => option.value.toLowerCase() === wanted);
  $dom.pageSetupSelect.value = match ? match.value : MANUAL_OPTION;
}

function renderMode() {
  $dom.outputFolderItem.style.display = $dom.modePdf.checked ? 'flex' : 'none';
}

$dom.pageSetupSelect.on('change', () => {
  if ($dom.pageSetupSelect.value === MANUAL_OPTION) return;
  $dom.pageSetup.value = $dom.pageSetupSelect.value;
  $settings.page_setup = $dom.pageSetupSelect.value;
});
$dom.refreshPageSetups.on('click', () => $websocket.sendToPlugin({ command: 'page_setups' }));
$dom.pageSetup.on('input', () => { $settings.page_setup = $dom.pageSetup.value; syncSelect(); });
[$dom.modeDevice, $dom.modePdf].forEach(radio => radio.on('change', () => {
  $settings.mode = $dom.modePdf.checked ? 'pdf' : 'device';
  renderMode();
}));
$dom.outputFolder.on('input', () => { $settings.output_folder = $dom.outputFolder.value; });
