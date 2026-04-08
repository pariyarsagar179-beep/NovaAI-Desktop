// -------------------------------
// CONFIG
// -------------------------------
const BACKEND_URL = "http://127.0.0.1:8000";

// -------------------------------
function $(id) {
    return document.getElementById(id);
}

// -------------------------------
let chartImages, chartQuestion, predictBtn, askChartBtn;
let pdfFile, uploadPdfBtn, refreshBtn, knowledgeList;
let pdfQuestion, askPdfBtn;
let chatMessages, clearChatBtn, welcomeName;

// -------------------------------
document.addEventListener("DOMContentLoaded", () => {
    console.log("Nova UI Loaded");

    chartImages = $("chartImages");
    chartQuestion = $("chartQuestion");
    predictBtn = $("predictBtn");
    askChartBtn = $("askChartBtn");

    pdfFile = $("pdfFile");
    uploadPdfBtn = $("uploadPdfBtn");
    refreshBtn = $("refreshBtn");
    knowledgeList = $("knowledgeList");

    pdfQuestion = $("pdfQuestion");
    askPdfBtn = $("askKnowledgeBtn");

    chatMessages = $("chatMessages");
    clearChatBtn = $("clearChatBtn");

    welcomeName = $("welcomeName");

    if (predictBtn) predictBtn.addEventListener("click", predictMarketMove);
    if (askChartBtn) askChartBtn.addEventListener("click", askAboutCharts);
    if (uploadPdfBtn) uploadPdfBtn.addEventListener("click", uploadPDF);
    if (refreshBtn) refreshBtn.addEventListener("click", loadKnowledgeList);
    if (askPdfBtn) askPdfBtn.addEventListener("click", askUsingPDFs);
    if (clearChatBtn) clearChatBtn.addEventListener("click", clearChat);

    loadKnowledgeList();
    setWelcomeName();
});

// -------------------------------
function setWelcomeName() {
    fetch(`${BACKEND_URL}/health`)
        .then(res => res.json())
        .then(data => {
            if (welcomeName) {
                welcomeName.textContent = data.username
                    ? `Welcome, ${data.username}`
                    : "Welcome";
            }
        })
        .catch(() => {});
}

// -------------------------------
function addMessage(sender, text) {
    const msg = document.createElement("div");
    msg.className = sender === "nova" ? "chat-bubble chat-ai" : "chat-bubble chat-user";
    msg.textContent = text;
    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function clearChat() {
    chatMessages.innerHTML = "";
}

// -------------------------------
async function predictMarketMove() {
    if (!chartImages.files.length) {
        addMessage("nova", "Please upload chart images first.");
        return;
    }

    const question = chartQuestion.value.trim();
    if (!question) {
        addMessage("nova", "Please enter a question.");
        return;
    }

    addMessage("user", "Predicting market move...");

    const formData = new FormData();
    for (let file of chartImages.files) {
        formData.append("images", file);
    }
    formData.append("question", question);

    try {
        const res = await fetch(`${BACKEND_URL}/predict`, {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        addMessage("nova", data.answer || "No response.");
    } catch {
        addMessage("nova", "Error contacting backend.");
    }
}

// -------------------------------
async function askAboutCharts() {
    if (!chartImages.files.length) {
        addMessage("nova", "Please upload chart images first.");
        return;
    }

    const question = chartQuestion.value.trim();
    if (!question) {
        addMessage("nova", "Please enter a question.");
        return;
    }

    addMessage("user", question);

    const formData = new FormData();
    for (let file of chartImages.files) {
        formData.append("images", file);
    }
    formData.append("question", question);

    try {
        const res = await fetch(`${BACKEND_URL}/ask_charts`, {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        addMessage("nova", data.answer || "No response.");
    } catch {
        addMessage("nova", "Error contacting backend.");
    }
}

// -------------------------------
async function uploadPDF() {
    if (!pdfFile.files.length) {
        addMessage("nova", "Please select a PDF file.");
        return;
    }

    addMessage("user", "Uploading PDF...");

    const formData = new FormData();
    formData.append("pdf", pdfFile.files[0]);

    try {
        const res = await fetch(`${BACKEND_URL}/upload_pdf`, {
            method: "POST",
            body: formData
        });
        const data = await res.json();

        addMessage("nova", `📘 ${pdfFile.files[0].name} learned successfully.`);
        loadKnowledgeList();
    } catch {
        addMessage("nova", "Error uploading PDF.");
    }
}

// -------------------------------
async function loadKnowledgeList() {
    knowledgeList.innerHTML = "<li>Loading...</li>";

    try {
        const res = await fetch(`${BACKEND_URL}/knowledge_files`);
        const data = await res.json();

        knowledgeList.innerHTML = "";

        if (!data.files || data.files.length === 0) {
            knowledgeList.innerHTML = "<li>No knowledge uploaded yet.</li>";
            return;
        }

        data.files.forEach(file => {
            const li = document.createElement("li");
            li.className = "knowledge-item";

            const nameDiv = document.createElement("div");
            nameDiv.className = "knowledge-name";
            nameDiv.innerHTML = `<span>📘</span> ${file}`;

            const delBtn = document.createElement("button");
            delBtn.textContent = "Delete";
            delBtn.className = "delete-btn";
            delBtn.addEventListener("click", () => deletePDF(file));

            li.appendChild(nameDiv);
            li.appendChild(delBtn);
            knowledgeList.appendChild(li);
        });

    } catch {
        knowledgeList.innerHTML = "<li>Error loading knowledge files.</li>";
    }
}

// -------------------------------
async function deletePDF(filename) {
    if (!confirm(`Delete ${filename}?`)) return;

    const formData = new FormData();
    formData.append("filename", filename);

    try {
        const res = await fetch(`${BACKEND_URL}/delete_pdf`, {
            method: "POST",
            body: formData
        });

        const data = await res.json();
        addMessage("nova", data.message || "Deleted.");

        loadKnowledgeList();
    } catch {
        addMessage("nova", "Error deleting PDF.");
    }
}

// -------------------------------
async function askUsingPDFs() {
    const question = pdfQuestion.value.trim();
    if (!question) return;

    addMessage("user", question);

    const formData = new FormData();
    formData.append("question", question);

    try {
        const res = await fetch(`${BACKEND_URL}/ask_pdf`, {
            method: "POST",
            body: formData
        });

        const data = await res.json();
        addMessage("nova", data.answer || "No response.");
    } catch {
        addMessage("nova", "Error contacting backend.");
    }
}