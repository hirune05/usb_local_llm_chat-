// p5.js のエントリポイント。
// グローバル状態は state.js、socket は socket-client.js、UI は chat-ui.js、
// 描画は face-animator.js / renderers/* に分離されている。

function initColorModal() {
  const modal = document.getElementById("color-modal");
  const groups = [
    { id: "swatches-face",  apply: (v) => { faceColor  = v; } },
    { id: "swatches-pupil", apply: (v) => { pupilColor = v; } },
  ];

  groups.forEach(({ id, apply }) => {
    const container = document.getElementById(id);
    const swatches = container.querySelectorAll(".swatch");
    swatches.forEach((swatch) => {
      swatch.style.background = swatch.dataset.color;
      swatch.addEventListener("click", () => {
        swatches.forEach((s) => s.classList.remove("selected"));
        swatch.classList.add("selected");
        apply(swatch.dataset.color);
        if (canvasCreated) redraw();
      });
    });
    // HTML の selected クラスで初期値を確定（HTML が唯一のデフォルト定義）
    const initial = container.querySelector(".swatch.selected");
    if (initial) apply(initial.dataset.color);
  });

  document.getElementById("color-modal-ok").addEventListener("click", () => {
    modal.classList.add("hidden");
    redraw();
  });
}

function setup() {
  let mainCanvas = createCanvas(1, 1);
  mainCanvas.hide();

  staticCanvas = createGraphics(540, 360);

  initColorModal();
  setupUIListeners();
  setupSocketListeners();

  rightCurrentParams = {
    eyeOpenness: 1,
    pupilSize: 0.7,
    pupilAngle: 0,
    upperEyelidAngle: 0,
    upperEyelidCoverage: 0,
    lowerEyelidCoverage: 0,
    mouthCurve: 0,
    mouthHeight: 0,
    mouthWidth: 1,
  };
  noLoop();
  setTimeout(() => {
    let staticHolder = document.getElementById("static-canvas-holder");
    staticHolder.appendChild(staticCanvas.canvas);
    canvasCreated = true;
    redraw();
  }, 100);
}

function draw() {
  if (!canvasCreated) return;
  drawStaticFace();
}

function setupUIListeners() {
  document.getElementById("chat-send").addEventListener("click", sendMessage);
  document.getElementById("chat-mic").addEventListener("click", toggleVoice);
  document.getElementById("chat-input").addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  });
}

// --- ブラウザコンソールから手動で表情を変えるためのデバッグヘルパ ---
function setExpression(v, a) {
  if (typeof v !== "number" || typeof a !== "number") {
    console.error(
      "Usage: setExpression(v, a) where v and a are numbers between -1.0 and 1.0"
    );
    return;
  }
  console.log(`Sending manual expression update: V=${v}, A=${a}`);
  socket.emit("manual_update_expression", { v: v, a: a });
}

window.setExpression = setExpression;
