document.addEventListener("DOMContentLoaded", function() {
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");

    // --- 1. SEND MESSAGE FUNCTION ---
    function sendMessage() {
        let message = userInput.value.trim();
        if (message === "") return;

        // Show User Message
        appendMessage("user-msg", message);
        userInput.value = "";

        // Send to Backend
        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            // Show Bot Message
            appendMessage("bot-msg", data.reply);

            // --- TRIGGERS ---
            if (data.show_breathing) {
                activateBreathing();
            }
            if (data.show_yoga) {
                activateYoga(data.yoga_tip, data.yoga_gif);
            }
        })
        .catch(error => {
            console.error("Error:", error);
            appendMessage("bot-msg", "⚠️ Error connecting to server.");
        });
    }

    // --- 2. HELPER FUNCTIONS ---
    function appendMessage(className, text) {
        let div = document.createElement("div");
        div.className = className;
        div.innerText = text;
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function activateBreathing() {
        let container = document.getElementById("breathing-container");
        let textElement = document.querySelector(".instruction-text"); // Class selector used here
        
        if(container) {
            container.style.display = "flex"; 
            
            // Text Loop Logic
            if(textElement) {
                textElement.innerText = "Inhale...";
                let breathInterval = setInterval(() => {
                    textElement.innerText = "Inhale...";
                    setTimeout(() => {
                        textElement.innerText = "Exhale...";
                    }, 2500); // Sync with CSS animation duration (5s total)
                }, 5000);

                // Stop after 15 seconds
                setTimeout(() => {
                    container.style.display = "none";
                    clearInterval(breathInterval);
                }, 15000);
            } else {
                // Fallback if text element missing
                setTimeout(() => { container.style.display = "none"; }, 7000);
            }
        }
    }

    function activateYoga(tip, gifUrl) {
        let card = document.getElementById("yoga-card");
        let instruction = document.getElementById("yoga-instruction");
        let visual = document.getElementById("yoga-visual");

        if (card && instruction && visual) {
            instruction.innerText = tip;
            // Use GIF from backend, or fallback
            visual.src = gifUrl || "https://media.giphy.com/media/1xVbRXc1wY5Jt6cOaN/giphy.gif";
            card.style.display = "block";
        }
    }

    // --- 3. EVENT LISTENERS (Yeh Miss Ho Gaye The) ---
    if (sendBtn) {
        sendBtn.addEventListener("click", sendMessage);
    }
    
    if (userInput) {
        userInput.addEventListener("keypress", function(event) {
            if (event.key === "Enter") {
                sendMessage();
            }
        });
    }
});

// --- 4. GLOBAL FUNCTION (Taaki HTML onclick isse access kar sake) ---
function closeYogaCard() {
    let card = document.getElementById("yoga-card");
    if (card) card.style.display = "none";
}