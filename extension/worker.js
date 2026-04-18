/**
 * Продакшен: false. Локальная разработка: true (бот на localhost:8080, дашборд localhost:3000).
 * На странице логина можно добавить ?loc=local — тоже включит локальный режим.
 */
const USE_LOCAL_DEV = false;
const AUTH_BASE_PROD = "https://bot.rustinfo.online";
const AUTH_BASE_LOCAL = "http://localhost:8080";
const DASHBOARD_LOCAL = "http://localhost:3000/dashboard.html";
const DASHBOARD_PROD = "https://rustinfo.online/dashboard.html";
const isLocalMode = (function () {
    if (typeof window === "undefined") return false;
    if (/[?&]loc=local\b/.test(window.location.search || "")) return true;
    return USE_LOCAL_DEV === true;
})();
const AUTH_BASE = isLocalMode ? AUTH_BASE_LOCAL : AUTH_BASE_PROD;
const DASHBOARD_URL = isLocalMode ? DASHBOARD_LOCAL : DASHBOARD_PROD;
const AUTH_GET_URL = AUTH_BASE + "/auth?token=TOKEN&steamId=STEAM_ID";
const AUTH_FCM_URL = AUTH_BASE + "/auth/fcm";
const delay = 100;
if (isLocalMode) {
    console.log("[RustInfo] DEV isLocalMode=1 DASHBOARD_URL=" + DASHBOARD_URL);
}

function looksLikeFcmData(obj) {
    if (!obj || typeof obj !== "object") return false;
    var hasToken = !!(obj.Token || obj.rustplus_auth_token);
    var hasExpo = !!(obj.ExpoPushToken || obj.expo_push_token);
    var hasFcm = !!(obj.fcm_credentials || (obj.fcm_token && obj.gcm_androidId));
    return hasToken && (hasExpo && hasFcm);
}

function extractFcmFields(msg) {
    if (!msg || typeof msg !== "object") return null;
    var m = msg.data || msg.payload || msg;
    if (m && typeof m === "object" && (m.data || m.payload)) m = m.data || m.payload;
    var expo = (m && m.ExpoPushToken) || (m && m.expo_push_token) || msg.ExpoPushToken || msg.expo_push_token;
    var fcmCreds = (m && m.fcm_credentials) || msg.fcm_credentials;
    if (!fcmCreds && m) {
        var f = (m.fcm_credentials && m.fcm_credentials.fcm) || (m.fcm && m.fcm);
        var g = (m.fcm_credentials && m.fcm_credentials.gcm) || {};
        if ((m.fcm_token || (f && f.token)) || (m.gcm_androidId || g.androidId)) {
            fcmCreds = {
                fcm: { token: (f && f.token) || m.fcm_token || "" },
                gcm: {
                    androidId: g.androidId || m.gcm_androidId || "",
                    securityToken: g.securityToken || m.gcm_securityToken || ""
                }
            };
        }
    }
    if (!fcmCreds && (msg.fcm_token || msg.gcm_androidId)) {
        fcmCreds = {
            fcm: { token: msg.fcm_token || "" },
            gcm: { androidId: msg.gcm_androidId || "", securityToken: msg.gcm_securityToken || "" }
        };
    }
    var token = (m && m.Token) || (m && m.rustplus_auth_token) || msg.Token || msg.rustplus_auth_token;
    var steamId = (m && m.SteamId) || (m && m.steam_id) || msg.SteamId || msg.steam_id || "";
    return { expo: expo, fcmCreds: fcmCreds, token: token, steamId: steamId };
}

function buildFcmBody(msg) {
    var x = extractFcmFields(msg);
    if (!x || !x.token) return null;
    if (x.expo && x.fcmCreds && x.fcmCreds.fcm && x.fcmCreds.fcm.token && x.fcmCreds.gcm && x.fcmCreds.gcm.androidId && x.fcmCreds.gcm.securityToken) {
        return {
            expo_push_token: x.expo,
            fcm_credentials: x.fcmCreds,
            rustplus_auth_token: x.token,
            steam_id: x.steamId
        };
    }
    return null;
}

function hasFullFcm(msg) {
    var x = extractFcmFields(msg);
    if (!x || !x.token) return false;
    var c = x.fcmCreds && x.fcmCreds.fcm && x.fcmCreds.fcm.token && x.fcmCreds.gcm && x.fcmCreds.gcm.androidId && x.fcmCreds.gcm.securityToken;
    return x.expo && !!c;
}

var _authHandled = false;
function handleAuthMessage(auth) {
    if (!auth || _authHandled) return;
    var token = auth.Token || auth.rustplus_auth_token || "";
    var steamId = auth.SteamId || auth.steam_id || "";
    if (!token) return;
    _authHandled = true;
    if (isLocalMode) {
        console.log("[RustInfo extension] Auth received (keys):", Object.keys(auth || {}));
    }
    var body = buildFcmBody(auth);
    var hasFull = body && hasFullFcm(auth);
    var payload = hasFull ? body : auth;
    if (isLocalMode) {
        console.log("[RustInfo extension] POST /auth/fcm:", hasFull ? "full FCM" : "raw object");
    }
    fetch(AUTH_FCM_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload)
    }).then(function(r) {
        if (!r.ok) {
            window.location.href = AUTH_GET_URL.replace("TOKEN", encodeURIComponent(token)).replace("STEAM_ID", encodeURIComponent(steamId));
            return;
        }
        return r.json();
    }).then(function(data) {
        if (!data) return;
        var redirect = isLocalMode ? DASHBOARD_URL : ((data && data.redirect) ? data.redirect : DASHBOARD_URL);
        window.location.href = redirect;
    }).catch(function() {
        window.location.href = AUTH_GET_URL.replace("TOKEN", encodeURIComponent(token)).replace("STEAM_ID", encodeURIComponent(steamId));
    });
}

function installInterceptor() {
    if (window.ReactNativeWebView === undefined) {
        window.ReactNativeWebView = {
            postMessage: function(message) {
                try {
                    var auth = typeof message === "string" ? JSON.parse(message) : message;
                    handleAuthMessage(auth);
                } catch (e) {
                    console.warn("[RustInfo extension] parse error:", e);
                }
            }
        };
    }
}
installInterceptor();
setInterval(installInterceptor, delay);

(function interceptFetch() {
    var origFetch = window.fetch;
    if (!origFetch) return;
    var ourHost = isLocalMode ? "localhost:8080" : "bot.rustinfo.online";
    window.fetch = function(url, opts) {
        var urlStr = (typeof url === "string" ? url : (url && url.url)) || "";
        if (urlStr && urlStr.indexOf(ourHost) >= 0) return origFetch.apply(this, arguments);
        var body = opts && opts.body;
        if (body && typeof body === "string") {
            try {
                var parsed = JSON.parse(body);
                if (looksLikeFcmData(parsed)) {
                    if (isLocalMode) console.log("[RustInfo] Captured FCM from fetch request:", Object.keys(parsed));
                    handleAuthMessage(parsed);
                }
            } catch (e) {}
        }
        return origFetch.apply(this, arguments).then(function(resp) {
            var clone = resp.clone();
            try {
                clone.json().then(function(data) {
                    if (data && looksLikeFcmData(data)) {
                        console.log("[RustInfo] Captured FCM from fetch response:", Object.keys(data));
                        handleAuthMessage(data);
                    }
                }).catch(function() {});
            } catch (e) {}
            return resp;
        }).catch(function(err) { return Promise.reject(err); });
    };
})();

(function interceptXHR() {
    var OrigXHR = window.XMLHttpRequest;
    if (!OrigXHR) return;
    var ourHost = isLocalMode ? "localhost:8080" : "bot.rustinfo.online";
    window.XMLHttpRequest = function() {
        var xhr = new OrigXHR();
        var xhrUrl = "";
        var origOpen = xhr.open;
        var origSend = xhr.send;
        xhr.open = function(method, url) {
            xhrUrl = url || "";
            return origOpen.apply(xhr, arguments);
        };
        xhr.send = function(body) {
            if (xhrUrl.indexOf(ourHost) < 0 && body && typeof body === "string") {
                try {
                    var parsed = JSON.parse(body);
                    if (looksLikeFcmData(parsed)) {
                        if (isLocalMode) console.log("[RustInfo] Captured FCM from XHR:", Object.keys(parsed));
                        handleAuthMessage(parsed);
                    }
                } catch (e) {}
            }
            return origSend.apply(xhr, arguments);
        };
        return xhr;
    };
})();

window.addEventListener("message", function(ev) {
    if (ev.source !== window || !ev.data) return;
    var d = ev.data;
    if (typeof d === "string") {
        try { d = JSON.parse(d); } catch (e) { return; }
    }
    if (d && (d.Token || d.rustplus_auth_token || (d.expo_push_token && d.fcm_credentials))) {
        handleAuthMessage(d);
    }
});