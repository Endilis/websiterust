/**
 * RustInfo integration for Glitchii/embedbuilder (MIT).
 * Parent dashboard reads window.json or uses postMessage rustinfo:getEmbed.
 */
(function () {
  function notifyReady() {
    if (window.parent === window) return;
    try {
      window.parent.postMessage({ type: 'rustinfo:embedbuilder-ready' }, '*');
    } catch (_) {}
  }

  addEventListener('DOMContentLoaded', notifyReady);
  if (document.readyState !== 'loading') notifyReady();

  addEventListener('message', (ev) => {
    const data = ev.data;
    if (!data || data.type !== 'rustinfo:getEmbed') return;
    let payload = null;
    let error = null;
    try {
      payload = window.json;
    } catch (e) {
      error = String(e && e.message ? e.message : e);
    }
    try {
      ev.source?.postMessage({
        type: 'rustinfo:embed',
        requestId: data.requestId,
        payload,
        error,
      }, ev.origin || '*');
    } catch (_) {}
  });
})();
