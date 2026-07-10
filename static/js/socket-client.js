// Socket.IO クライアント。サーバーからのイベントを受け取り、状態と UI を更新する。

// 接続先を指定しない場合、今開いているページと同じホスト:ポートに接続される。
// ポートをハードコードすると APP_PORT を変えたときにチャット・音声が全滅するので固定しない。
const socket = io();

function setupSocketListeners() {
  let botMessageDiv = null;

  socket.on("connect", () => {
    console.log("サーバーに接続しました。");
  });

  socket.on("bot_stream", (data) => {
    if (!botMessageDiv) {
      botMessageDiv = addMessageToHistory("", "bot-message");
    }
    botMessageDiv.innerHTML += data.chunk.replace(/\n/g, "<br>");
    const chatHistory = document.getElementById("chat-history");
    chatHistory.scrollTop = chatHistory.scrollHeight;
  });

  socket.on("bot_stream_end", (data) => {
    messages.push({ role: "assistant", content: data.text });
    trimMessages();
    if (data.emotion) {
      lastEmotion = data.emotion;
      console.log("Saved emotion:", lastEmotion);
    }
    botMessageDiv = null;
  });

  socket.on("update_expression", (params) => {
    console.log("Received update_expression event:", params);
    rightTargetParams = params;
    console.log("rightTargetParams after update_expression:", rightTargetParams);
    rightAnimationDuration = 1000;
    rightStartParams = { ...rightCurrentParams };
    rightAnimationStartTime = millis();
    rightAnimationActive = true;
    loop();
  });

  socket.on("update_mouth", (data) => {
    mouthAnimDuration = data.duration;
    mouthAnimStartValue = mouthOverride;
    mouthAnimTargetValue = data.openness;
    mouthAnimStartTime = millis();
    mouthAnimActive = true;
    loop();
  });

  socket.on("save_success", (data) => {
    alert(data.message);
  });

  socket.on("save_error", (data) => {
    alert("保存エラー: " + data.message);
  });

  socket.on("voice_status", (data) => {
    updateMicButton(data.status);
  });

  socket.on("voice_transcript", (data) => {
    const text = (data.text || "").trim();
    if (!text) {
      addMessageToHistory("音声が検出できませんでした。", "bot-message error");
      return;
    }
    const input = document.getElementById("chat-input");
    input.value = text;
    input.focus();
  });

  socket.on("voice_error", (data) => {
    updateMicButton("idle");
    addMessageToHistory(`音声エラー: ${data.message}`, "bot-message error");
  });

  socket.on("error", (data) => {
    console.error("サーバーエラー:", data.message);
    addMessageToHistory(`サーバーエラー: ${data.message}`, "bot-message error");
  });
}
