// static/script.js

const chatContainer = document.getElementById("chatContainer");
const userInput = document.getElementById("userInput");
const typingIndicator = document.getElementById("typing");

function handleKeyPress(event) {
  if (event.key === "Enter") {
    event.preventDefault();
    sendMessage();
  }
}

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  // 1. Show User Message
  addMessage(text, "user");
  userInput.value = "";
  
  // 2. Show Typing Indicator
  typingIndicator.style.display = "block";
  chatContainer.scrollTop = chatContainer.scrollHeight;

  try {
    // 3. SEND TO PYTHON BACKEND (The Connection)
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }) // Sending data to app.py
    });

    const data = await response.json();

    // 4. Hide Typing & Show AI Response
    typingIndicator.style.display = "none";
    addMessage(data.reply, "bot");

  } catch (error) {
    typingIndicator.style.display = "none";
    addMessage("I'm having trouble connecting to the server. Please try again.", "bot");
    console.error("Error:", error);
  }
}

function addMessage(text, sender) {
  const div = document.createElement("div");
  div.className = `message ${sender}`;
  div.innerText = text;
  chatContainer.appendChild(div);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}