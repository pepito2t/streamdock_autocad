const DEFAULT_MODULE = 'dwg-parts';
const $local = false, $back = false,
  $dom = {
    main: $('.sdpi-wrapper'),
    module: $('#module'),
    refreshModules: $('#refresh-modules'),
    projectFromName: $('#project-from-name'),
    message: $('#message'),
  },
  $propEvent = {
    didReceiveSettings() {
      $dom.projectFromName.checked = $settings.project_from_name !== false;
      renderModules([]);
    },
    sendToPropertyInspector(data) {
      if (data.event === 'modules') {
        renderModules(data.modules);
        if (data.message) $dom.message.textContent = data.message;
        return;
      }
      handleNotice(data);
    },
  };

function renderModules(modules) {
  const wanted = $settings.module || DEFAULT_MODULE;
  $dom.module.innerHTML = '';
  const known = modules.length ? modules : [{ id: wanted, name: `${wanted} (Drawflow fermée)` }];
  known.forEach(module => {
    const option = document.createElement('option');
    option.value = module.id;
    option.textContent = module.name;
    $dom.module.appendChild(option);
  });
  $dom.module.value = known.some(module => module.id === wanted) ? wanted : known[0].id;
}

$dom.module.on('change', () => { $settings.module = $dom.module.value; });
$dom.refreshModules.on('click', () => $websocket.sendToPlugin({ command: 'modules' }));
$dom.projectFromName.on('change', () => { $settings.project_from_name = $dom.projectFromName.checked; });
