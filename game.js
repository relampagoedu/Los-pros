const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");
const scoreEl = document.getElementById("score");
const timeEl = document.getElementById("time");
const overlay = document.getElementById("overlay");
const messageEl = document.getElementById("message");
const startButton = document.getElementById("startButton");

const gameState = {
  player: { x: 320, y: 180, radius: 14, speed: 3.2 },
  star: { x: 120, y: 80, radius: 10 },
  score: 0,
  timeLeft: 30,
  running: false,
  timerId: null,
  keys: new Set(),
};

const resetGame = () => {
  gameState.player.x = canvas.width / 2;
  gameState.player.y = canvas.height / 2;
  gameState.score = 0;
  gameState.timeLeft = 30;
  scoreEl.textContent = gameState.score;
  timeEl.textContent = gameState.timeLeft;
  spawnStar();
};

const spawnStar = () => {
  const padding = 30;
  gameState.star.x = padding + Math.random() * (canvas.width - padding * 2);
  gameState.star.y = padding + Math.random() * (canvas.height - padding * 2);
};

const drawBackground = () => {
  ctx.fillStyle = "#0f172a";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  for (let i = 0; i < 40; i += 1) {
    ctx.fillStyle = `rgba(255, 255, 255, ${Math.random()})`;
    ctx.beginPath();
    ctx.arc(
      Math.random() * canvas.width,
      Math.random() * canvas.height,
      Math.random() * 1.5 + 0.3,
      0,
      Math.PI * 2
    );
    ctx.fill();
  }
};

const drawPlayer = () => {
  ctx.fillStyle = "#38bdf8";
  ctx.beginPath();
  ctx.arc(gameState.player.x, gameState.player.y, gameState.player.radius, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#f8fafc";
  ctx.beginPath();
  ctx.arc(gameState.player.x - 5, gameState.player.y - 3, 3, 0, Math.PI * 2);
  ctx.fill();
};

const drawStar = () => {
  ctx.fillStyle = "#fbbf24";
  ctx.beginPath();
  ctx.moveTo(gameState.star.x, gameState.star.y - gameState.star.radius);
  for (let i = 1; i < 5; i += 1) {
    const angle = (Math.PI * 2 * i) / 5 - Math.PI / 2;
    const radius = i % 2 === 0 ? gameState.star.radius : gameState.star.radius * 0.45;
    ctx.lineTo(
      gameState.star.x + Math.cos(angle) * radius,
      gameState.star.y + Math.sin(angle) * radius
    );
  }
  ctx.closePath();
  ctx.fill();
};

const handleMovement = () => {
  const { player, keys } = gameState;
  if (keys.has("ArrowUp") || keys.has("w")) player.y -= player.speed;
  if (keys.has("ArrowDown") || keys.has("s")) player.y += player.speed;
  if (keys.has("ArrowLeft") || keys.has("a")) player.x -= player.speed;
  if (keys.has("ArrowRight") || keys.has("d")) player.x += player.speed;

  player.x = Math.max(player.radius, Math.min(canvas.width - player.radius, player.x));
  player.y = Math.max(player.radius, Math.min(canvas.height - player.radius, player.y));
};

const checkCollision = () => {
  const dx = gameState.player.x - gameState.star.x;
  const dy = gameState.player.y - gameState.star.y;
  const distance = Math.hypot(dx, dy);
  if (distance < gameState.player.radius + gameState.star.radius) {
    gameState.score += 5;
    scoreEl.textContent = gameState.score;
    spawnStar();
  }
};

const update = () => {
  if (!gameState.running) return;
  handleMovement();
  checkCollision();

  drawBackground();
  drawStar();
  drawPlayer();

  requestAnimationFrame(update);
};

const endGame = () => {
  gameState.running = false;
  clearInterval(gameState.timerId);
  overlay.classList.remove("hidden");
  messageEl.textContent = `¡Tiempo! Tu puntuación fue ${gameState.score}`;
  startButton.textContent = "Jugar otra vez";
};

const startGame = () => {
  resetGame();
  gameState.running = true;
  overlay.classList.add("hidden");
  messageEl.textContent = "";
  startButton.textContent = "Jugar";

  gameState.timerId = setInterval(() => {
    gameState.timeLeft -= 1;
    timeEl.textContent = gameState.timeLeft;
    if (gameState.timeLeft <= 0) {
      endGame();
    }
  }, 1000);

  update();
};

startButton.addEventListener("click", () => {
  if (!gameState.running) startGame();
});

window.addEventListener("keydown", (event) => {
  if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "w", "a", "s", "d"].includes(event.key)) {
    event.preventDefault();
    gameState.keys.add(event.key);
  }
});

window.addEventListener("keyup", (event) => {
  gameState.keys.delete(event.key);
});

drawBackground();
drawStar();
drawPlayer();
