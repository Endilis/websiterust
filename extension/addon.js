const inj = document.createElement('script');
inj.onload = function() {
    this.remove();
};
inj.src = chrome.runtime.getURL('worker.js');
const el = document.head || document.documentElement;
if (el) el.appendChild(inj);
const desc = document.querySelector("body > div > div > div.overlay-body > p");
if (desc) {
    desc.style.color = "#2ac5ed";
    desc.innerHTML = "Continue logging in below to allow <b>RustInfo Bot</b> to send and receive team chat messages.";
}