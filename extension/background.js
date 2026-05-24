const clicked = chrome.action.onClicked;
clicked.addListener(() => {
    const tabs = chrome.tabs;
    tabs.create({url: "https://companion-rust.facepunch.com/login"});
});

chrome.runtime.onMessageExternal.addListener((message, _sender, sendResponse) => {
    if (message && message.type === 'ping') {
        sendResponse({ ok: true, version: chrome.runtime.getManifest().version });
        return true;
    }
    return false;
});
