function handleKeyPress(event) {
  if (event.key === "Enter") {
    event.preventDefault();
    sendMessage();
  }
}

function sendMessage() {
  const input = document.getElementById("userInput");
  const text = input.value.trim();
  if (!text) return;

  addMessage(text, "user");
  input.value = "";

  showTyping();

  setTimeout(() => {
    hideTyping();
    const emotion = detectEmotion(text);
    addMessage(getResponse(emotion), "bot");

    const exercise = getExercise(emotion);
    if (exercise) {
      setTimeout(() => {
        addMessage(exercise, "bot");
      }, 600);
    }
  }, 900);
}

function addMessage(text, sender) {
  const chat = document.getElementById("chatContainer");
  const div = document.createElement("div");
  div.className = `message ${sender}`;
  div.innerText = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function showTyping() {
  document.getElementById("typing").style.display = "block";
}

function hideTyping() {
  document.getElementById("typing").style.display = "none";
}

function detectEmotion(msg) {
  msg = msg.toLowerCase();

  if (msg.includes("suicide") || msg.includes("die"))
    return "crisis";
  if (msg.includes("angry") || msg.includes("frustrated"))
    return "angry";
  if (msg.includes("anxious") || msg.includes("panic"))
    return "anxious";
  if (msg.includes("sad") || msg.includes("lonely"))
    return "sad";
  if (msg.includes("tired") || msg.includes("burnt"))
    return "tired";

  return "neutral";
}

function getResponse(emotion) {
  const responses = {
    angry: "It sounds like there’s a lot of anger here. That’s okay. Let’s slow this moment down.",
    anxious: "Your mind seems overwhelmed right now. You’re not alone in this.",
    sad: "That feels really heavy. Thank you for trusting me with it.",
    tired: "You sound exhausted. Even acknowledging that takes strength.",
    neutral: "I’m here. Take your time and say whatever you need.",
    crisis:
      "I’m really sorry you’re feeling this way. You deserve immediate support. Please reach out to someone you trust or local emergency services."
  };
  return responses[emotion];
}

function getExercise(emotion) {
  const exercises = {
    angry:
      "Try grounding: press your feet into the floor and unclench your jaw.",
    anxious:
      "Let’s breathe together: inhale 4 seconds, hold 4, exhale 6.",
    sad:
      "Name one thing around you that feels comforting.",
    tired:
      "Pause for 30 seconds and let your shoulders relax."
  };
  return exercises[emotion] || null;
}
