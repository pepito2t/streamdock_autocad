// Shared by every property inspector: update banner and last-error line, injected above the form.
const $notice = (() => {
  const wrapper = document.querySelector('.sdpi-wrapper');
  const item = document.createElement('div');
  item.className = 'sdpi-item notice';
  item.innerHTML = '<div class="sdpi-item-label"></div><div class="sdpi-item-value"><div id="notice-update"></div><div id="notice-error"></div></div>';
  wrapper.prepend(item);
  return { update: item.querySelector('#notice-update'), error: item.querySelector('#notice-error') };
})();

function handleNotice(data) {
  if (data.event === 'update') {
    $notice.update.innerHTML = '';
    const link = document.createElement('a');
    link.href = '#';
    link.textContent = `Mise à jour ${data.version} disponible`;
    link.addEventListener('click', event => { event.preventDefault(); $websocket.openUrl(data.url); });
    $notice.update.appendChild(link);
    return true;
  }
  if (data.event === 'error') {
    $notice.error.textContent = data.message || '';
    return true;
  }
  return false;
}

function clearError() {
  $notice.error.textContent = '';
}
