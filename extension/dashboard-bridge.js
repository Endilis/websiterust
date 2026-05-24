/** Сигнал для панели rustinfo.online: расширение установлено. */
document.documentElement.dataset.rustinfoExtension = '1';
window.dispatchEvent(new CustomEvent('rustinfo-extension-ready'));
