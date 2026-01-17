document.addEventListener("DOMContentLoaded", function() {
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const micBtn = document.getElementById("mic-btn"); // 🔥 New Mic Button
    const savedChatsBtn = document.getElementById("saved-chats-btn");
    const historyList = document.getElementById("history-list");
    const newChatBtn = document.getElementById("new-chat-btn");
    const ventingBtn = document.getElementById("venting-btn");

    // Global Flag
    let isVentingMode = false;

    // 1. PAGE LOAD: Restore History
    restoreChatHistory();

    function restoreChatHistory() {
        if (isVentingMode) return;
        fetch("/get_history_api")
        .then(res => res.json())
        .then(data => {
            if (data.success && data.history.length > 0) {
                chatBox.innerHTML = '<div class="text-center text-xs text-gray-400 my-4">--- Session Restored ---</div>';
                let chatHistory = data.history.reverse(); 
                chatHistory.forEach(chat => {
                    appendMessage("user-msg", chat.message);
                    let botReply = `I understand. (${chat.emotion})`;
                    appendMessage("bot-msg", botReply);
                });
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        })
        .catch(err => console.log("History error:", err));
    }

    // 🔥 2. MIC BUTTON LOGIC (Voice to Text)
    if (micBtn) {
        // Browser Check
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = false; // Ek sentence ke baad ruk jayega
            recognition.lang = 'en-US'; // English (India ke liye 'en-IN' bhi kar sakte ho)

            micBtn.addEventListener("click", function() {
                if (micBtn.classList.contains("mic-active")) {
                    recognition.stop(); // Agar on hai toh band karo
                } else {
                    recognition.start(); // Start recording
                }
            });

            // Start Event
            recognition.onstart = function() {
                micBtn.classList.add("mic-active"); // CSS Pulse Animation On
                userInput.placeholder = "Listening...";
            };

            // End Event
            recognition.onend = function() {
                micBtn.classList.remove("mic-active"); // Animation Off
                userInput.placeholder = "Type your message...";
                userInput.focus();
            };

            // Result Event (Text mil gaya)
            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                userInput.value = transcript; // Input box mein text daalo
                // Optional: Auto send karna hai toh neeche wali line uncomment karo
                // sendMessage(); 
            };
        } else {
            // Agar browser support nahi karta
            micBtn.style.display = "none";
            console.log("Web Speech API not supported in this browser.");
        }
    }

    // 3. SAVED CHATS SIDEBAR
    if (savedChatsBtn && historyList) {
        savedChatsBtn.addEventListener("click", function() {
            if(isVentingMode) {
                alert("Please exit Venting Mode first (Click New Chat).");
                return;
            }
            historyList.innerHTML = '<div class="text-xs text-gray-500 px-2">Loading...</div>';
            fetch("/get_history_api")
            .then(res => res.json())
            .then(data => {
                historyList.innerHTML = ""; 
                if (data.success && data.history.length > 0) {
                    data.history.forEach(chat => {
                        let item = document.createElement("button");
                        item.className = "text-left text-sm text-gray-700 p-2 hover:bg-white/40 rounded-lg transition duration-200 truncate w-full flex items-center mb-1";
                        let icon = "📝";
                        let em = chat.emotion || "Neutral"; 
                        if(em.includes("Sad")) icon = "🌧️";
                        if(em.includes("Happy")) icon = "☀️";
                        if(em.includes("Angry")) icon = "🔥";
                        let dateStr = chat.timestamp.split(" ")[0];
                        item.innerHTML = `<span class="mr-2">${icon}</span> <span class="truncate">${dateStr} • ${em}</span>`;
                        item.addEventListener("click", function() {
                            chatBox.innerHTML = "";
                            let header = document.createElement("div");
                            header.className = "text-center text-gray-500 text-xs my-4";
                            header.innerText = `--- Memory from ${chat.timestamp} ---`;
                            chatBox.appendChild(header);
                            appendMessage("user-msg", chat.message);
                            setTimeout(() => { appendMessage("bot-msg", `I remember you felt ${em} that day.`); }, 500);
                        });
                        historyList.appendChild(item);
                    });
                } else {
                    historyList.innerHTML = '<div class="text-xs text-gray-500 px-2">No history.</div>';
                }
            });
        });
    }

    // 4. VENTING MODE
    if (ventingBtn) {
        ventingBtn.addEventListener("click", function() {
            isVentingMode = true;
            chatBox.innerHTML = ''; 
            let header = document.createElement("div");
            header.className = "text-center text-gray-500 text-xs my-4";
            header.innerText = "--- 🔒 VENTING MODE (Not Saving) ---";
            chatBox.appendChild(header);
            let title = document.getElementById("header-title"); 
            if(title) {
                title.innerText = "Venting Mode 🔒";
                title.style.color = "#e74c3c";
            }
            appendMessage("bot-msg", "I am listening. Let it all out. Nothing you say here will be saved.");
        });
    }

    // 5. SEND MESSAGE & LOGIC
    function sendMessage() {
        let message = userInput.value.trim();
        if (message === "") return;

        appendMessage("user-msg", message);
        userInput.value = "";

        let msg = message.toLowerCase();
        if (msg.includes("sad") || msg.includes("lonely")) setMood("mood-sad", "audio-rain");
        else if (msg.includes("happy") || msg.includes("excited")) setMood("mood-happy", "audio-birds");
        else if (msg.includes("stress") || msg.includes("anxious")) setMood("mood-stressed", "audio-stream");
        else if (msg.includes("angry")) setMood("mood-angry", "audio-fire");

        fetch("/chat_api", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                message: message,
                is_venting: isVentingMode
            })
        })
        .then(res => res.json())
        .then(data => {
            appendMessage("bot-msg", data.reply);
            if (data.show_breathing) activateBreathing();
        })
        .catch(e => {
            appendMessage("bot-msg", "⚠️ Error connecting.");
        });
    }

    function appendMessage(cls, text) {
        let div = document.createElement("div");
        div.className = cls;
        div.innerText = text;
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    sendBtn.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (e) => { if(e.key==="Enter") sendMessage(); });

    // 6. NEW CHAT
    if(newChatBtn) {
        newChatBtn.addEventListener("click", function() {
            if(confirm("Start fresh?")) {
                isVentingMode = false;
                let title = document.getElementById("header-title");
                if(title) { 
                    title.innerText = "Serene"; 
                    title.style.color = ""; 
                }
                chatBox.innerHTML = '<div class="bot-msg">Hello! I am here to listen. How are you feeling?</div>';
                document.body.className = "";
                stopSounds();
            }
        });
    }

    // HELPER FUNCTIONS
    function activateBreathing() {
        let box = document.getElementById("breathing-container");
        let txt = document.getElementById("breath-text");
        if(box) {
            box.style.display = "flex";
            if(txt) txt.innerText = "Inhale...";
            setTimeout(() => { box.style.display = "none"; }, 16000);
        }
    }

    function setMood(cls, audioId) {
        document.body.className = cls;
        stopSounds();
        let audio = document.getElementById(audioId);
        if(audio) audio.play().catch(e=>console.log("Audio block"));
    }

    function stopSounds() {
        document.querySelectorAll("audio").forEach(a => { a.pause(); a.currentTime = 0; });
    }
});