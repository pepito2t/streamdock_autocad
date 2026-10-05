const $local = false, $back = false,
  $dom = {
    main: $('.sdpi-wrapper'),
    modePreset: $('#mode-preset'),
    modeCustom: $('#mode-custom'),
    presetSection: $('#preset-section'),
    customSection: $('#custom-section'),
    preset: $('#preset'),
    presetDescription: $('#preset-description'),
    editPreset: $('#edit-preset'),
    deletePreset: $('#delete-preset'),
    steps: $('#steps'),
    saveName: $('#save-name'),
    savePreset: $('#save-preset'),
    message: $('#message'),
  };

let presets = [];

const $propEvent = {
  didReceiveSettings() {
    $dom.modeCustom.checked = $settings.mode === 'custom';
    $dom.modePreset.checked = !$dom.modeCustom.checked;
    $dom.steps.value = $settings.steps || '';
    renderPresets();
    renderMode();
    $websocket.sendToPlugin({ command: 'list' });
  },
  sendToPropertyInspector(data) {
    if (data.event === 'presets') {
      presets = data.presets;
      renderPresets();
      showMessage('');
    } else if (data.event === 'error') {
      showMessage(data.message);
    }
  },
};

function currentPreset() {
  return presets.find(preset => preset.id === $dom.preset.value);
}

function renderPresets() {
  $dom.preset.innerHTML = '';
  presets.forEach(preset => {
    const option = document.createElement('option');
    option.value = preset.id;
    option.textContent = preset.builtin ? preset.name : `${preset.name} (perso)`;
    $dom.preset.appendChild(option);
  });
  if ($settings && presets.some(preset => preset.id === $settings.preset)) {
    $dom.preset.value = $settings.preset;
  } else if (presets.length && $settings) {
    $settings.preset = $dom.preset.value;
  }
  renderPresetDetails();
}

function renderPresetDetails() {
  const preset = currentPreset();
  $dom.presetDescription.textContent = preset ? preset.description : '';
  $dom.deletePreset.disabled = !preset || preset.builtin;
}

function renderMode() {
  const custom = $dom.modeCustom.checked;
  $dom.presetSection.style.display = custom ? 'none' : 'block';
  $dom.customSection.style.display = custom ? 'block' : 'none';
}

function showMessage(text) {
  $dom.message.textContent = text;
}

[$dom.modePreset, $dom.modeCustom].forEach(radio => radio.on('change', () => {
  $settings.mode = $dom.modeCustom.checked ? 'custom' : 'preset';
  renderMode();
}));

$dom.preset.on('change', () => {
  $settings.preset = $dom.preset.value;
  renderPresetDetails();
});

$dom.steps.on('input', () => { $settings.steps = $dom.steps.value; });

$dom.editPreset.on('click', () => {
  const preset = currentPreset();
  if (!preset) return;
  $dom.steps.value = preset.steps.join('\n');
  $dom.saveName.value = preset.builtin ? `${preset.name} (copie)` : preset.name;
  $settings.steps = $dom.steps.value;
  $settings.mode = 'custom';
  $dom.modeCustom.checked = true;
  renderMode();
});

$dom.deletePreset.on('click', () => {
  const preset = currentPreset();
  if (!preset || preset.builtin) return;
  $websocket.sendToPlugin({ command: 'delete', id: preset.id });
});

$dom.savePreset.on('click', () => {
  const name = $dom.saveName.value.trim();
  if (!name) {
    showMessage('Donne un nom au preset.');
    return;
  }
  $websocket.sendToPlugin({ command: 'save', macro: { name, steps: $dom.steps.value } });
});
