const $local = false, $back = false,
  $dom = {
    main: $('.sdpi-wrapper'),
  },
  $propEvent = {
    didReceiveSettings() {},
    sendToPropertyInspector(data) {
      handleNotice(data);
    },
  };
