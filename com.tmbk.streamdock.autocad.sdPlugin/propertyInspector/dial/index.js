const $local = false, $back = false,
  $dom = {
    main: $('.sdpi-wrapper'),
    function: $('#function'),
  },
  $propEvent = {
    didReceiveSettings() {
      $dom.function.value = $settings.function || 'zoom';
    },
    sendToPropertyInspector(data) {
      handleNotice(data);
    },
  };

$dom.function.on('change', () => { $settings.function = $dom.function.value; });
