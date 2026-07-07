// チャット UI（履歴表示、入力、マイクボタン）

function trimMessages() {
  if (messages.length > MAX_MESSAGES) {
    messages = messages.slice(-MAX_MESSAGES);
  }
}

function addMessageToHistory(text, className) {
  const chatHistory = document.getElementById("chat-history");
  const messageDiv = document.createElement("div");
  messageDiv.className = `chat-message ${className}`;
  messageDiv.innerText = text;
  chatHistory.appendChild(messageDiv);
  chatHistory.scrollTop = chatHistory.scrollHeight;
  return messageDiv;
}

function sendTextMessage(text) {
  const trimmed = text.trim();
  if (trimmed === "") return;

  addMessageToHistory(trimmed, "user-message");
  messages.push({ role: "user", content: trimmed });
  trimMessages();

  socket.emit("user_message", {
    // 履歴なし計測モード: 一時無効化
    // messages: [{ role: "user", content: trimmed }],
    // last_emotion: null,
    messages: messages,
    last_emotion: lastEmotion,
  });
}

function sendMessage() {
  const input = document.getElementById("chat-input");
  const text = input.value.trim();
  if (text === "") return;

  sendTextMessage(text);
  input.value = "";
}

function toggleVoice() {
  if (!voiceRecording) {
    socket.emit("voice_start");
    return;
  }
  socket.emit("voice_stop");
}

function updateMicButton(status) {
  const button = document.getElementById("chat-mic");
  if (!button) return;

  if (status === "recording") {
    voiceRecording = true;
    button.classList.add("recording");
    button.disabled = false;
    button.textContent = "停止";
    return;
  }

  if (status === "processing") {
    button.disabled = true;
    button.textContent = "処理中";
    return;
  }

  voiceRecording = false;
  button.classList.remove("recording");
  button.disabled = false;
  button.textContent = "録音";
}
