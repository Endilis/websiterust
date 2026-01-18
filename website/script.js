const WORKER_URL = "https://stats.rustinfo.online";

async function fetchWorker() {
  const messageEl = document.getElementById("workerMessage");
  const statusTitle = document.getElementById("statusTitle");
  const statusDot = document.getElementById("statusDot");
  const latency = document.getElementById("latency");
  const updated = document.getElementById("updated");

  const started = performance.now();
  messageEl.textContent = "Загрузка…";
  statusTitle.textContent = "Проверяем...";
  statusDot.style.background = "#f6d14a";

  try {
    const res = await fetch(WORKER_URL);
    const text = await res.text();
    const ms = Math.round(performance.now() - started);

    latency.textContent = `latency: ${ms} ms`;
    updated.textContent = `обновлено: ${new Date().toLocaleTimeString()}`;

    statusTitle.textContent = res.ok ? "Воркера отвечает" : "Ответ с ошибкой";
    statusDot.style.background = res.ok ? "#8ddf5f" : "#f97a6a";
    messageEl.textContent = text;
  } catch (e) {
    statusTitle.textContent = "Нет ответа";
    statusDot.style.background = "#f97a6a";
    messageEl.textContent = "Ошибка загрузки данных";
    latency.textContent = "latency: —";
  }
}

function copyResponse() {
  const text = document.getElementById("workerMessage").textContent;
  navigator.clipboard.writeText(text).catch(() => {});
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("refreshBtn").addEventListener("click", fetchWorker);
  document.getElementById("copyBtn").addEventListener("click", copyResponse);
  document.getElementById("pingBtn").addEventListener("click", fetchWorker);
  fetchWorker();
});
