document.addEventListener("DOMContentLoaded", function() {
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const micBtn = document.getElementById("mic-btn");
    const savedChatsBtn = document.getElementById("saved-chats-btn");
    const historyList = document.getElementById("history-list");
    const newChatBtn = document.getElementById("new-chat-btn");
    const ventingBtn = document.getElementById("venting-btn");

    let isVentingMode = false;
    let currentUtterance = null;

    // 1. PAGE LOAD
    restoreChatHistory();

    function restoreChatHistory() {
        if (isVentingMode) return;
        fetch("/get_history_api")
        .then(res => res.json())
        .then(data => {
            if (data.success && data.history.length > 0) {
                chatBox.innerHTML = '<div class="text-center text-xs text-gray-400 my-4">--- Session Restored ---</div>';
                let chatHistory = data.history.reverse(); 
                
                // Last chat ka emotion utha ke theme set kar do
                if(chatHistory.length > 0) {
                    let lastEmotion = chatHistory[chatHistory.length - 1].emotion;
                    updateTheme(lastEmotion); // 🔥 Restore theme based on last chat
                }

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

    // 2. SEND MESSAGE (The Logic Change)
    function sendMessage() {
        let message = userInput.value.trim();
        if (message === "") return;

        appendMessage("user-msg", message);
        userInput.value = "";

        // ❌ Pehle hum yahan local check karte the, ab nahi karenge.
        // Hum wait karenge API response ka.

        // Show typing indicator (Optional improvement)
        let loadingDiv = document.createElement("div");
        loadingDiv.className = "text-xs text-gray-400 ml-4 mb-2";
        loadingDiv.innerText = "Serene is thinking...";
        loadingDiv.id = "typing-indicator";
        chatBox.appendChild(loadingDiv);
        chatBox.scrollTop = chatBox.scrollHeight;

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
            // Remove typing indicator
            let loader = document.getElementById("typing-indicator");
            if(loader) loader.remove();

            appendMessage("bot-msg", data.reply);
            
            // 🔥 REAL AI THEME CHANGE
            // Backend se jo 'emotion' aaya, usse theme update karo
            if (!isVentingMode) {
                updateTheme(data.emotion);
            }

            if (data.show_breathing) activateBreathing();
        })
        .catch(e => {
            console.log(e);
            let loader = document.getElementById("typing-indicator");
            if(loader) loader.remove();
            appendMessage("bot-msg", "⚠️ Error connecting.");
        });
    }

    // 🔥 NEW FUNCTION: Theme Manager based on AI Emotion
    function updateTheme(emotion) {
        if(!emotion) return;
        
        let em = emotion.toLowerCase();
        console.log("AI Detected Emotion:", em);

        // Reset Sounds
        stopSounds();

        // Logic Mapping
        if (em.includes("sad") || em.includes("lonely") || em.includes("grief") || em.includes("depressed")) {
            setMood("mood-sad", "audio-rain");
        } 
        else if (em.includes("happy") || em.includes("excited") || em.includes("joy") || em.includes("grateful")) {
            setMood("mood-happy", "audio-birds");
        } 
        else if (em.includes("stress") || em.includes("anxious") || em.includes("fear") || em.includes("overwhelmed")) {
            setMood("mood-stressed", "audio-stream");
        } 
        else if (em.includes("angry") || em.includes("frustrated") || em.includes("mad")) {
            setMood("mood-angry", "audio-fire");
        }
        else if (em.includes("tired") || em.includes("exhausted")) {
            setMood("mood-tired", "audio-night");
        }
        else {
            // Neutral or Unknown
            document.body.className = ""; // Default Theme
        }
    }

    // ... Baaki Helper Functions same rahenge (appendMessage, setMood, etc.) ...
    
    function appendMessage(cls, text) {
        let msgContainer = document.createElement("div");
        msgContainer.className = cls + " flex flex-col"; 
        
        let textDiv = document.createElement("div");
        textDiv.innerText = text;
        msgContainer.appendChild(textDiv);

        let footerDiv = document.createElement("div");
        footerDiv.className = "flex justify-end mt-1"; 

        let speakBtn = document.createElement("button");
        speakBtn.className = "text-gray-400 hover:text-gray-600 transition focus:outline-none p-1";
        speakBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
            </svg>
        `;
        speakBtn.addEventListener("click", function() { toggleSpeech(text, speakBtn); });

        footerDiv.appendChild(speakBtn);
        msgContainer.appendChild(footerDiv);
        chatBox.appendChild(msgContainer);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function toggleSpeech(text, btn) {
        window.speechSynthesis.cancel();
        document.querySelectorAll(".speaking-active").forEach(el => {
            el.classList.remove("text-blue-500", "speaking-active");
            el.classList.add("text-gray-400");
        });

        if (currentUtterance === text) {
            currentUtterance = null;
            return; 
        }

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'en-US';
        
        btn.classList.remove("text-gray-400");
        btn.classList.add("text-blue-500", "speaking-active");
        currentUtterance = text;

        utterance.onend = function() {
            btn.classList.remove("text-blue-500", "speaking-active");
            btn.classList.add("text-gray-400");
            currentUtterance = null;
        };

        window.speechSynthesis.speak(utterance);
    }

    function setMood(cls, audioId) {
        document.body.className = cls;
        let audio = document.getElementById(audioId);
        if(audio) audio.play().catch(e=>console.log("Audio block"));
    }

    function stopSounds() {
        document.querySelectorAll("audio").forEach(a => { a.pause(); a.currentTime = 0; });
    }

    // Mic, Sidebar, Venting, New Chat listeners (Copy from previous code)
    if (micBtn) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.lang = 'en-US';
            micBtn.addEventListener("click", function() {
                if (micBtn.classList.contains("mic-active")) recognition.stop();
                else recognition.start();
            });
            recognition.onstart = function() { micBtn.classList.add("mic-active"); };
            recognition.onend = function() { micBtn.classList.remove("mic-active"); };
            recognition.onresult = function(event) {
                userInput.value = event.results[0][0].transcript;
                sendMessage();
            };
        } else { micBtn.style.display = "none"; }
    }

    if (ventingBtn) {
        ventingBtn.addEventListener("click", function() {
            isVentingMode = true;
            chatBox.innerHTML = ''; 
            let header = document.createElement("div");
            header.className = "text-center text-gray-500 text-xs my-4";
            header.innerText = "--- 🔒 VENTING MODE ---";
            chatBox.appendChild(header);
            let title = document.getElementById("header-title"); 
            if(title) { title.innerText = "Venting Mode 🔒"; title.style.color = "#e74c3c"; }
            appendMessage("bot-msg", "I am listening. Let it all out.");
        });
    }

    if(newChatBtn) {
        newChatBtn.addEventListener("click", function() {
            if(confirm("Start fresh?")) {
                isVentingMode = false;
                window.speechSynthesis.cancel();
                let title = document.getElementById("header-title");
                if(title) { title.innerText = "Zen AI"; title.style.color = ""; }
                chatBox.innerHTML = '<div class="bot-msg">Hello! I am here to listen.</div>';
                document.body.className = "";
                stopSounds();
            }
        });
    }

    // Sidebar Logic
    if (savedChatsBtn && historyList) {
        savedChatsBtn.addEventListener("click", function() {
            if(isVentingMode) { alert("Exit Venting Mode first."); return; }
            historyList.innerHTML = '<div class="text-xs text-gray-500 px-2">Loading...</div>';
            fetch("/get_history_api").then(res => res.json()).then(data => {
                historyList.innerHTML = ""; 
                if (data.success && data.history.length > 0) {
                    data.history.forEach(chat => {
                        let item = document.createElement("button");
                        item.className = "text-left text-sm text-gray-700 p-2 hover:bg-white/40 rounded-lg transition duration-200 truncate w-full flex items-center mb-1";
                        let icon = "📝";
                        if((chat.emotion || "").includes("Sad")) icon = "🌧️";
                        let dateStr = chat.timestamp.split(" ")[0];
                        item.innerHTML = `<span class="mr-2">${icon}</span> <span class="truncate">${dateStr} • ${chat.emotion}</span>`;
                        item.addEventListener("click", function() {
                            chatBox.innerHTML = "";
                            let header = document.createElement("div");
                            header.className = "text-center text-gray-500 text-xs my-4";
                            header.innerText = `--- Memory from ${chat.timestamp} ---`;
                            chatBox.appendChild(header);
                            appendMessage("user-msg", chat.message);
                            setTimeout(() => { appendMessage("bot-msg", `I remember: ${chat.emotion}`); }, 500);
                        });
                        historyList.appendChild(item);
                    });
                } else { historyList.innerHTML = '<div class="text-xs text-gray-500 px-2">No history.</div>'; }
            });
        });
    }
    
    // Delete Button Logic
    const deleteBtn = document.getElementById("delete-btn"); 
    if (deleteBtn) {
        deleteBtn.addEventListener("click", function() {
            if (confirm("Delete ALL history?")) {
                fetch("/delete_history_api", { method: "POST" })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        chatBox.innerHTML = '<div class="bot-msg">History cleared.</div>';
                        if(historyList) historyList.innerHTML = '<div class="text-xs text-gray-500 px-2">No history.</div>';
                    }
                });
            }
        });
    }

    sendBtn.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (e) => { if(e.key==="Enter") sendMessage(); });
    
    function activateBreathing() {
        let box = document.getElementById("breathing-container");
        if(box) { box.style.display = "flex"; setTimeout(() => { box.style.display = "none"; }, 16000); }
    }
});