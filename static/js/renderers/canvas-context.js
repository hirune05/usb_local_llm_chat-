// p5.js のグローバル描画関数を一時的にオフスクリーンキャンバス向けにすり替えるヘルパ。
// renderers/eye-renderer.js, mouth-renderer.js が global API（ellipse, arc など）に依存しているため、
// このブリッジで static canvas に出力させている。

function setupContext(canvas) {
  const original = {
    push: window.push,
    pop: window.pop,
    translate: window.translate,
    fill: window.fill,
    stroke: window.stroke,
    strokeWeight: window.strokeWeight,
    ellipse: window.ellipse,
    arc: window.arc,
    rotate: window.rotate,
    radians: window.radians,
    rect: window.rect,
    line: window.line,
    noFill: window.noFill,
    noStroke: window.noStroke,
    beginShape: window.beginShape,
    vertex: window.vertex,
    endShape: window.endShape,
    curveVertex: window.curveVertex,
    width: window.width,
    height: window.height,
    drawingContext: window.drawingContext,
    abs: window.abs,
    asin: window.asin,
    cos: window.cos,
    sin: window.sin,
    PI: window.PI,
    TWO_PI: window.TWO_PI,
    CLOSE: window.CLOSE,
  };
  window.push = () => canvas.push();
  window.pop = () => canvas.pop();
  window.translate = (x, y) => canvas.translate(x, y);
  window.fill = (...args) => canvas.fill(...args);
  window.stroke = (...args) => canvas.stroke(...args);
  window.strokeWeight = (w) => canvas.strokeWeight(w);
  window.ellipse = (x, y, w, h) => canvas.ellipse(x, y, w, h);
  window.arc = (x, y, w, h, start, stop, mode) =>
    canvas.arc(x, y, w, h, start, stop, mode);
  window.rotate = (angle) => canvas.rotate(angle);
  window.radians = (degrees) => canvas.radians(degrees);
  window.rect = (x, y, w, h) => canvas.rect(x, y, w, h);
  window.line = (x1, y1, x2, y2) => canvas.line(x1, y1, x2, y2);
  window.noFill = () => canvas.noFill();
  window.noStroke = () => canvas.noStroke();
  window.beginShape = () => canvas.beginShape();
  window.vertex = (x, y) => canvas.vertex(x, y);
  window.endShape = (mode) => canvas.endShape(mode);
  window.curveVertex = (x, y) => canvas.curveVertex(x, y);
  window.width = canvas.width;
  window.height = canvas.height;
  window.drawingContext = canvas.canvas.getContext("2d");
  return original;
}

function restoreContext(original) {
  Object.keys(original).forEach((key) => {
    window[key] = original[key];
  });
}
