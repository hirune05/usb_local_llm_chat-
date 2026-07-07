// 表情・口パクアニメーションと描画

function drawStaticFace() {
  staticCanvas.background(faceColor);
  staticCanvas.push();
  staticCanvas.translate(staticCanvas.width / 2, staticCanvas.height / 2);

  if (rightAnimationActive) {
    updateRightAnimation();
  }
  if (mouthAnimActive) {
    updateMouthAnimation();
  }

  console.log(
    "drawStaticFace - drawing with rightCurrentParams:",
    rightCurrentParams
  );

  const drawParams = {
    ...rightCurrentParams,
    mouthHeight: Math.max(
      0,
      Math.min(3.5, rightCurrentParams.mouthHeight + mouthOverride)
    ),
    faceColor,
    pupilColor,
    scleraColor,
  };

  let originalCtx = setupContext(staticCanvas);
  drawEyes(drawParams);
  drawMouth(drawParams);
  restoreContext(originalCtx);

  staticCanvas.pop();
}

function updateRightAnimation() {
  const currentTime = millis();
  const elapsed = currentTime - rightAnimationStartTime;
  const progress = Math.min(elapsed / rightAnimationDuration, 1);
  const easeProgress =
    progress < 0.5
      ? 2 * progress * progress
      : 1 - Math.pow(-2 * progress + 2, 2) / 2;

  for (let key in rightTargetParams) {
    if (rightStartParams[key] !== undefined) {
      rightCurrentParams[key] = lerp(
        rightStartParams[key],
        rightTargetParams[key],
        easeProgress
      );
    }
  }

  if (rightAnimationActive) {
    console.log(
      "updateRightAnimation - progress:",
      progress.toFixed(2),
      "rightCurrentParams:",
      rightCurrentParams
    );
  }

  if (progress >= 1) {
    rightAnimationActive = false;
    console.log(
      "Animation finished. Final rightCurrentParams:",
      rightCurrentParams
    );
    if (!mouthAnimActive) {
      noLoop();
    }
  }
}

function updateMouthAnimation() {
  const currentTime = millis();
  const elapsed = currentTime - mouthAnimStartTime;
  const progress = Math.min(elapsed / mouthAnimDuration, 1);
  const easeProgress =
    progress < 0.5
      ? 2 * progress * progress
      : 1 - Math.pow(-2 * progress + 2, 2) / 2;

  mouthOverride = lerp(mouthAnimStartValue, mouthAnimTargetValue, easeProgress);

  if (progress >= 1) {
    mouthAnimActive = false;
    if (!rightAnimationActive) {
      noLoop();
    }
  }
}
