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

            // --- A. MOOD AMBIENCE LOGIC (Frontend Instant Trigger) ---
            let msg = message.toLowerCase();

            if (msg.includes("sad") || msg.includes("lonely") || msg.includes("depressed") || msg.includes("cry")) {
                setMood("mood-sad", "audio-rain");
            } 
            else if (msg.includes("happy") || msg.includes("excited") || msg.includes("good") || msg.includes("joy")) {
                setMood("mood-happy", "audio-birds");
            }
            else if (msg.includes("stress") || msg.includes("anxious") || msg.includes("panic") || msg.includes("nervous")) {
                setMood("mood-stressed", "audio-stream");
            }
            else if (msg.includes("angry") || msg.includes("mad") || msg.includes("furious") || msg.includes("hate")) {
                setMood("mood-angry", "audio-fire");
            }
            else if (msg.includes("tired") || msg.includes("sleepy") || msg.includes("exhausted")) {
                setMood("mood-tired", "audio-night");
            }
            
            // --- B. FEATURE TRIGGERS (Backend Logic) ---
            // (Yeh part tumne miss kar diya tha, ab wapas daal diya hai)
            
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
        let textElement = document.querySelector(".instruction-text");
        
        if(container) {
            container.style.display = "flex"; 
            
            // Animation Loop logic
            if(textElement) {
                textElement.innerText = "Inhale...";
                let breathInterval = setInterval(() => {
                    textElement.innerText = "Inhale...";
                    setTimeout(() => {
                        textElement.innerText = "Exhale...";
                    }, 2500); 
                }, 5000);

                // Stop after 15 seconds
                setTimeout(() => {
                    container.style.display = "none";
                    clearInterval(breathInterval);
                }, 15000);
            } else {
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
            visual.src = gifUrl || "https://media.giphy.com/media/1xVbRXc1wY5Jt6cOaN/giphy.gif";
            card.style.display = "block";
        }
    }

    // --- 3. EVENT LISTENERS ---
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

// --- 4. GLOBAL FUNCTIONS (Accessible by HTML onclick) ---

function closeYogaCard() {
    let card = document.getElementById("yoga-card");
    if (card) card.style.display = "none";
}

function setMood(moodClass, audioId) {
    // 1. Reset Body Classes
    document.body.className = ""; 
    
    // 2. Add New Mood Class
    if (moodClass) {
        document.body.classList.add(moodClass);
    }

    // 3. Audio Management
    stopAllSounds();
    if (audioId) {
        let audio = document.getElementById(audioId);
        if (audio) {
            audio.volume = 0.5;
            audio.play().catch(e => console.log("Audio autoplay blocked via browser settings"));
        }
    }
}

function stopAllSounds() {
    const sounds = ["audio-rain", "audio-birds", "audio-stream", "audio-fire", "audio-night"];
    sounds.forEach(id => {
        let audio = document.getElementById(id);
        if (audio) {
            audio.pause();
            audio.currentTime = 0;
        }
    });
}