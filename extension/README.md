# RustInfo Bot — Chrome extension

ID: `bnmfocbcaaaimljcchgplaceimiaglha`
Store: <https://chromewebstore.google.com/detail/rustinfo-bot/bnmfocbcaaaimljcchgplaceimiaglha>

Manifest V3, service worker + один content script, инжектящий `worker.js` на страницу
`https://companion-rust.facepunch.com/*`.

## Файлы

- `manifest.json` — Manifest V3. `content_scripts` матчит только `companion-rust.facepunch.com/*`.
- `background.js` — service worker. По клику на иконку открывает `companion-rust.facepunch.com/login`.
- `addon.js` — content script, инжектит `worker.js` в DOM страницы и подменяет текст в overlay.
- `worker.js` — основная логика перехвата авторизации Rust+.
- `icons/` — иконки 16/32/48/64/128/256.

## Что и откуда ловит `worker.js`

Скрипт ставит три перехватчика на странице `companion-rust.facepunch.com`:

1. **`window.ReactNativeWebView.postMessage`** — Rust+ Companion использует этот объект
   (через React Native WebView). Подмена самого объекта/метода ловит колбэк авторизации.
2. **`window.fetch`** — оборачивается, инспектирует request body и response JSON.
3. **`XMLHttpRequest.send`** — аналогично для XHR.
4. **`window.addEventListener("message", …)`** — запасной канал через `postMessage`
   между iframe/окон.

Для каждого перехваченного объекта проверяется `looksLikeFcmData()` / `extractFcmFields()`
и собирается каноничный body.

## Какие данные отправляет (`POST /auth/fcm`)

`buildFcmBody()` формирует **плоский** JSON (`worker.js:62-74`):

```json
{
  "expo_push_token": "ExponentPushToken[...]",
  "fcm_credentials": {
    "fcm": { "token": "…" },
    "gcm": { "androidId": "…", "securityToken": "…" }
  },
  "rustplus_auth_token": "<Rust+ JWT>",
  "steam_id": "<SteamID64>"
}
```

Если не удалось собрать полный набор FCM-полей — отправляется «сырое» тело сообщения
(raw `auth`-объект).

### Да, `steam_id` присылается отдельно от токена

В теле POST-а `steam_id` — самостоятельное поле. Берётся из `auth.SteamId` или
`auth.steam_id` (`worker.js:58` и `worker.js:87`). Также SteamID зашит внутри JWT
Rust+ токена (его можно достать декодированием `rustplus_auth_token`), но расширение
их шлёт явно.

### Discord ID в теле не шлётся

Расширение **не знает** Discord ID пользователя. Запрос идёт с `credentials: "include"`,
так что сервер должен сопоставить Rust+/Steam с Discord-аккаунтом по сессионной cookie,
выставленной ранее при логине через Discord OAuth (`/discord/callback`).

## Fallback при отсутствии endpoint-а

Если `POST /auth/fcm` вернул не-2xx ответ, расширение делает редирект:

```
window.location.href = `${AUTH_BASE}/auth?token=<token>&steamId=<steam_id>`
```

(`worker.js:106, 115`). Этот GET-обработчик уже реализован в `web_panel.py::handle_auth`
и сохраняет в таблицу `rust_tokens`: `steam_id`, `token`, `created_at`, `discord_id`
(из сессии). **При этом `expo_push_token` и `fcm_credentials` теряются** —
их через fallback не передать.

## Режимы

- **Prod** (`USE_LOCAL_DEV = false`): обращается к `https://bot.rustinfo.online`,
  редирект на `https://rustinfo.online/dashboard.html`.
- **Local dev** (`USE_LOCAL_DEV = true` или добавить `?loc=local` к URL логина):
  `http://localhost:8080` + `http://localhost:3000/dashboard.html`.

## Публикация / сборка

Никаких билд-скриптов; папка загружается как есть:
- Chrome Web Store (текущая версия 1.0) — для пользователей.
- Developer mode → Load unpacked (указать эту папку) — для локальной отладки.
