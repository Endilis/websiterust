export default {
  async fetch(request, env) {
    // Берём данные из KV
    let stats = await env.STATS.get("serverData") // ключ в KV
    if (!stats) {
      // если ещё нет, возвращаем пример
      stats = JSON.stringify({
        players: 0,
        status: "offline"
      })
    }

    return new Response(stats, {
      headers: { "Content-Type": "application/json" }
    })
  }
}
