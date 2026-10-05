const $local = false, $back = false,
  $dom = {
    main: $('.sdpi-wrapper'),
    layer: $('#layer'),
    create: $('#create'),
  },
  $propEvent = {
    didReceiveSettings() {
      $dom.layer.value = $settings.layer || '';
      $dom.create.checked = $settings.create !== false;
    },
  };

$dom.layer.on('input', () => { $settings.layer = $dom.layer.value; });
$dom.create.on('change', () => { $settings.create = $dom.create.checked; });
