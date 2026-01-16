document.addEventListener("DOMContentLoaded", function() {
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");

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
                activateYoga(data.yoga_tip);
            }
        })
        .catch(error => {
            console.error(error);
            appendMessage("bot-msg", "⚠️ Error connecting to server.");
        });
    }

    function appendMessage(className, text) {
        let div = document.createElement("div");
        div.className = className;
        div.innerText = text;
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function activateBreathing() {
        let container = document.getElementById("breathing-container");
        container.style.display = "flex"; // CSS flex to center
        setTimeout(() => {
            container.style.display = "none";
        }, 7000); // 7 seconds duration
    }

    function activateYoga(tip) {
        let card = document.getElementById("yoga-card");
        document.getElementById("yoga-instruction").innerText = tip;
        card.style.display = "block";
    }

    // Event Listeners
    sendBtn.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });
});

function closeYogaCard() {
    document.getElementById("yoga-card").style.display = "none";
}