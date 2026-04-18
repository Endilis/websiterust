const clicked = chrome.action.onClicked;
clicked.addListener(() => {
    const tabs = chrome.tabs;
    tabs.create({url: "https://companion-rust.facepunch.com/login"});
});