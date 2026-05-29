const askBtn = document.getElementById("askBtn");
const questionInput = document.getElementById("question");
const retrievalModeInput = document.getElementById("retrievalMode");
const rerankModeInput = document.getElementById("rerankMode");
const topKInput = document.getElementById("topK");
const answerBox = document.getElementById("answer");
const metricsBox = document.getElementById("metrics");
const sourcesList = document.getElementById("sources");
const API_KEY = window.prompt("Enter demo API key:");
const API_BASE_URL = "https://ca-knowledgerk-api.kindglacier-855f7384.canadacentral.azurecontainerapps.io";


function renderMetrics(data) {
  metricsBox.innerHTML = `
    <div><strong>Retrieval Mode:</strong> ${data.retrieval_mode ?? "n/a"}</div>
    <div><strong>Rerank Mode:</strong> ${data.rerank_mode ?? "n/a"}</div>
    <div><strong>Top K:</strong> ${data.top_k ?? "n/a"}</div>
    <div><strong>Raw Results:</strong> ${data.raw_result_count ?? "n/a"}</div>
    <div><strong>Filtered Results:</strong> ${data.filtered_result_count ?? "n/a"}</div>
    <div><strong>Reranked Results:</strong> ${data.reranked_result_count ?? "n/a"}</div>
    <div><strong>Final Context Chunks:</strong> ${data.final_context_count ?? "n/a"}</div>
    <div><strong>Prompt Tokens:</strong> ${data.prompt_tokens ?? "n/a"}</div>
    <div><strong>Completion Tokens:</strong> ${data.completion_tokens ?? "n/a"}</div>
    <div><strong>Total Tokens:</strong> ${data.total_tokens ?? "n/a"}</div>
    <div><strong>Estimated Cost:</strong> ${
      data.estimated_cost_usd !== undefined && data.estimated_cost_usd !== null
        ? `$${data.estimated_cost_usd}`
        : "n/a"
    }</div>
    <div><strong>Latency:</strong> ${
      data.latency_ms !== undefined && data.latency_ms !== null
        ? `${data.latency_ms} ms`
        : "n/a"
    }</div>
  `;
}

function renderSources(sources) {
  sourcesList.innerHTML = "";

  if (sources && sources.length > 0) {
    sources.forEach((source) => {
      const li = document.createElement("li");
      li.textContent =
        `${source.title} | ${source.chunk_id}` +
        (source.effective_date ? ` | ${source.effective_date}` : "") +
        (source.score !== undefined && source.score !== null
          ? ` | score: ${source.score}`
          : "");
      sourcesList.appendChild(li);
    });
  } else {
    const li = document.createElement("li");
    li.textContent = "No sources found.";
    sourcesList.appendChild(li);
  }
}

askBtn.addEventListener("click", async () => {
  const question = questionInput.value.trim();
  const retrievalMode = retrievalModeInput.value;
  const rerankMode = rerankModeInput.value;
  const topK = Number(topKInput.value);

  if (!question) {
    answerBox.textContent = "Please enter a question.";
    metricsBox.textContent = "No metrics yet.";
    sourcesList.innerHTML = "";
    return;
  }

  answerBox.textContent = "Loading...";
  metricsBox.textContent = "Loading metrics...";
  sourcesList.innerHTML = "";

  try {
    const response = await fetch(`${API_BASE_URL}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
      },
      body: JSON.stringify({
        question: question,
        retrieval_mode: retrievalMode,
        rerank_mode: rerankMode,
        top_k: topK
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const data = await response.json();

    answerBox.textContent = data.answer || "No answer returned.";
    renderMetrics(data);
    renderSources(data.sources);
  } catch (error) {
    answerBox.textContent = `Error: ${error.message}`;
    metricsBox.textContent = "Metrics unavailable due to error.";
  }
});