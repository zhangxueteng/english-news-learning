const corsHeaders = {
  "Access-Control-Allow-Origin": "https://zhangxueteng.github.io",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
  "Content-Type": "application/json; charset=utf-8"
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: corsHeaders });
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders });
    }
    if (origin && origin !== "https://zhangxueteng.github.io") {
      return json({ error: "Origin not allowed" }, 403);
    }
    if (request.method !== "POST") return json({ error: "Use POST" }, 405);
    if (!env.OPENAI_API_KEY) return json({ error: "Server API key is not configured" }, 500);

    let body;
    try { body = await request.json(); } catch { return json({ error: "Invalid JSON" }, 400); }

    const text = String(body.text || "").trim().slice(0, 5000);
    const context = String(body.context || "").trim().slice(0, 2500);
    const task = String(body.task || "translate");
    if (!text) return json({ error: "Text is required" }, 400);
    if (!["translate", "word"].includes(task)) return json({ error: "Unsupported task" }, 400);

    const instructions = task === "word"
      ? "你是一位专业的英语教师，面向中文母语学习者。结合上下文解释目标英文单词或短语。请用简体中文，简洁但具体地输出：1. 本句中的准确含义；2. 词性/短语结构；3. 常见其他含义（仅在有帮助时）；4. 一条例句及中文。若是俚语、口语、讽刺或固定搭配，要解释真实语用含义，不要逐字硬译。不要臆造信息。"
      : "你是一位专业的中英双语翻译。把英文翻译成自然、准确、符合语境的简体中文。保留原意、语气和人物关系；口语、俚语、习语按实际含义翻译，不要逐字硬译。只输出译文，不要添加开场白或解释。";

    const input = task === "word"
      ? "需要解释的词/短语：" + text + "\n上下文：" + (context || "未提供")
      : "需要翻译的英文：" + text + "\n上下文：" + (context || "未提供");

    try {
      const upstream = await fetch("https://api.openai.com/v1/responses", {
        method: "POST",
        headers: {
          "Authorization": "Bearer " + env.OPENAI_API_KEY,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          model: env.OPENAI_MODEL || "gpt-5-mini",
          instructions,
          input,
          max_output_tokens: task === "word" ? 500 : 700,
          store: false
        })
      });
      const data = await upstream.json();
      if (!upstream.ok) {
        return json({ error: data.error?.message || "OpenAI API request failed" }, upstream.status);
      }
      const output = (data.output || [])
        .filter(item => item.type === "message")
        .flatMap(item => item.content || [])
        .filter(item => item.type === "output_text")
        .map(item => item.text)
        .join("\n")
        .trim();
      if (!output) return json({ error: "No text returned from OpenAI" }, 502);
      return json({ result: output, model: data.model || env.OPENAI_MODEL || "gpt-5-mini" });
    } catch {
      return json({ error: "Could not connect to OpenAI API" }, 502);
    }
  }
};
