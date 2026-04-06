const askBtn = document.getElementById("askBtn");
const questionInput = document.getElementById("question");
const retrievalModeInput = document.getElementById("retrievalMode");
const topKInput = document.getElementById("topK");
const answerBox = document.getElementById("answer");
const sourcesList = document.getElementById("sources");

askBtn.addEventListener("click", async () => {
  const question = questionInput.value.trim();
  const retrievalMode = retrievalModeInput.value;
  const topK = Number(topKInput.value);

  if (!question) {
    answerBox.textContent = "Please enter a question.";
    sourcesList.innerHTML = "";
    return;
  }

  answerBox.textContent = "Loading...";
  sourcesList.innerHTML = "";

  try {
    const response = await fetch("http://127.0.0.1:8000/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        question: question,
        retrieval_mode: retrievalMode,
        top_k: topK
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const data = await response.json();

    answerBox.textContent = data.answer || "No answer returned.";

    if (data.sources && data.sources.length > 0) {
      data.sources.forEach((source) => {
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
  } catch (error) {
    answerBox.textContent = `Error: ${error.message}`;
  }
});