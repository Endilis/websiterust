// Временно используем тестовый Worker URL
const WORKER_URL = "https://rustinfo-stats.YOUR_SUBDOMAIN.workers.dev";

async function load() {
  try {
    const res = await fetch(WORKER_URL);
    const text = await res.text();
    document.getElementById("workerMessage").textContent = text;
  } catch (e) {
    document.getElementById("workerMessage").textContent = "Ошибка: " + e;
  }
}

load();
