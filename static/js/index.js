let latestMarkdown = ''; // variabile globale per conservare il Markdown

// Funzione per inviare il testo al server Flask per la traduzione
async function sendTextForTranslation() {
    const text = document.getElementById('textInput').value;
    const model = document.getElementById('llm').value;
    const language = document.getElementById('targetLang').options[document.getElementById('targetLang').selectedIndex].text;

    if (!text.trim()) {
        alert("Please enter text to translate.");
        return;
    }

    const spinner = document.getElementById('loadingSpinner');
    spinner.style.display = 'block'; // Mostra lo spinner

    try {
        const response = await fetch('/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                model: model,
                language: language
            })
        });

        const data = await response.json();

        if (data.response) {
            latestMarkdown = data.translation;

            const streamEl = document.getElementById('modelStream');
            streamEl.innerHTML = marked.parse(data.translation);

            renderMathInElement(streamEl, {
                delimiters: [
                    {left: "$$", right: "$$", display: true},
                    {left: "\\[", right: "\\]", display: true},
                    {left: "$", right: "$", display: false},
                    {left: "\\(", right: "\\)", display: false}
                ]
            });

        } else {
            document.getElementById('modelStream').textContent = data.message || "Translation failed.";
        }

    } catch (error) {
        document.getElementById('modelStream').textContent = "Error: " + error;
    } finally {
        spinner.style.display = 'none'; // Nascondi lo spinner sempre alla fine
    }
}




function clearTextInput() {
    document.getElementById('textInput').value = '';
    latestMarkdown = ''; // Resetta il Markdown
    document.getElementById('fileInput').value = ''; // Resetta il file input
}


function clearTextOutput() {
    document.getElementById('modelStream').innerText = '';
    latestMarkdown = ''; // Resetta il Markdown
}

// Funzione per copiare l'output negli appunti
function copyOutput() {
    const output = document.getElementById('modelStream').innerText;
    if (!output) return;
    navigator.clipboard.writeText(output);
}

// Funzione per scaricare l'output come file 
function downloadOutput() {
    if (!latestMarkdown) {
        alert("Nessun contenuto da scaricare.");
        return;
    }
    const blob = new Blob([latestMarkdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'translation.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}


document.addEventListener("DOMContentLoaded", function () {
    fetch("/llmList", {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        if (data.response && data.models && Array.isArray(data.models)) {
            const llmSelect = document.getElementById("llm");
            llmSelect.innerHTML = ""; // Svuota la select

            data.models.forEach(modelName => {
                const option = document.createElement("option");
                option.value = modelName;
                option.textContent = modelName;
                llmSelect.appendChild(option);
            });
        } else {
            console.error("Modelli non ricevuti correttamente:", data);
        }
    })
    .catch(err => {
        console.error("Errore durante il caricamento dei modelli:", err);
    });

    clearTextInput();
    clearTextOutput();
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        document.body.classList.add('darkmode');
        document.getElementById('toggleThemeBtn').innerText = "☀️";
    } else {
        document.body.classList.remove('darkmode');
        document.getElementById('toggleThemeBtn').innerText = "🌙";
    }
});

function loadFile() {
    const fileInput = document.getElementById('fileInput');
    const textArea = document.getElementById('textInput');

    if (!fileInput.files.length) return;

    const file = fileInput.files[0];
    const fileType = file.type || '';

    // Simple check: process text/markdown client-side, upload all else
    if (fileType.startsWith('text/') || file.name.endsWith('.md')) {
        const reader = new FileReader();

        reader.onload = (event) => {
            const content = event.target.result;
            textArea.value = content;
        };

        reader.readAsText(file);
    } else {
        // Non-text file: upload the raw file to the server
        sendFileToServer(file);
    }
}

function sendFileToServer(file) {
   alert("Not implemented yet. Please upload text files or markdown files directly.");
}



function toggleTheme() {
    const body = document.body;
    const btn = document.getElementById('toggleThemeBtn');
    const isDark = body.classList.toggle('darkmode');
    if (isDark) {
        btn.innerText = "☀️";
        localStorage.setItem('theme', 'dark');
    } else {
        btn.innerText = "🌙";
        localStorage.setItem('theme', 'light');
    }
}