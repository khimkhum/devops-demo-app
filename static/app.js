const button = document.getElementById('checkApi');
button.addEventListener('click', async () => {
  button.disabled = true;
  button.textContent = 'Đang kiểm tra…';
  const start = performance.now();
  let success = false;
  let message;
  try {
    const response = await fetch('/health', { cache: 'no-store', signal: AbortSignal.timeout(5000) });
    const data = await response.json();
    success = response.ok && data.status === 'ok';
    message = JSON.stringify(data, null, 2);
    document.getElementById('latency').textContent = Math.round(performance.now() - start);
  } catch (error) {
    message = 'Không kết nối được API: ' + error.message;
    document.getElementById('latency').textContent = '—';
  } finally {
    document.getElementById('healthState').textContent = success ? 'HEALTHY' : 'ERROR';
    document.getElementById('healthNote').textContent = success ? 'API đang phản hồi thành công.' : 'Kiểm tra thất bại. Xem chi tiết trong console bên dưới.';
    document.getElementById('apiOutput').textContent = message;
    const item = document.createElement('li');
    item.className = 'live-feed-item';
    for (const [className, text] of [
      ['feed-time', new Date().toLocaleTimeString('vi-VN')],
      ['feed-event', 'GET /health'], ['feed-source', 'browser'],
      ['feed-status ' + (success ? 'ok' : 'err'), success ? 'SUCCESS' : 'ERROR']
    ]) {
      const span = document.createElement('span');
      span.className = className;
      span.textContent = text;
      item.appendChild(span);
    }
    const list = document.getElementById('eventList');
    list.prepend(item);
    while (list.children.length > 8) list.lastElementChild.remove();
    button.disabled = false;
    button.textContent = 'Kiểm tra API ↗';
  }
});
