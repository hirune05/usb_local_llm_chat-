// アプリ全体で共有するグローバル状態
// 既存スタイルに合わせて window 上に直接生やす（モジュール化はしない）

// p5.js キャンバス
let staticCanvas;
let canvasCreated = false;

// 表情パラメータ
let rightCurrentParams = {};
let rightTargetParams = {};
let rightStartParams = {};

// 表情アニメーション
let rightAnimationActive = false;
let rightAnimationStartTime = null;
let rightAnimationDuration = 1000;

// 会話履歴・直近の感情
let messages = [];
const MAX_TURNS = 5;
const MAX_MESSAGES = MAX_TURNS * 2;
let lastEmotion = null;

// 外見カラー設定（CSS hex文字列。initColorModal でピッカー値に上書きされる）
let faceColor = '#ffebfa';
let pupilColor = '#000000';
let scleraColor = '#f0fff0';

// その他 UI 状態
let currentEmotion = "normal";
let savedEmotions = new Set();
let voiceRecording = false;

// 口パク（音声同期）
let mouthOverride = 0;
let mouthAnimActive = false;
let mouthAnimStartTime = null;
let mouthAnimDuration = 80;
let mouthAnimStartValue = 0;
let mouthAnimTargetValue = 0;
