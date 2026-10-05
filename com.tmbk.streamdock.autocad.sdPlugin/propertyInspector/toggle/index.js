const $local = false, $back = false,
  $dom = {
    main: $('.sdpi-wrapper'),
    variable: $('#variable'),
  },
  $propEvent = {
    didReceiveSettings() {
      $dom.variable.value = $settings.variable || 'ORTHOMODE';
    },
    sendToPropertyInspector(data) {
      handleNotice(data);
    },
  };

$dom.variable.on('change', () => { $settings.variable = $dom.variable.value; });
