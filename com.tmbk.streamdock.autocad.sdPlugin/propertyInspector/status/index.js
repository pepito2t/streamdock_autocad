const $local = false, $back = false,
  $dom = {
    main: $('.sdpi-wrapper'),
    field: $('#field'),
  },
  $propEvent = {
    didReceiveSettings() {
      $dom.field.value = $settings.field || 'layer';
    },
  };

$dom.field.on('change', () => { $settings.field = $dom.field.value; });
