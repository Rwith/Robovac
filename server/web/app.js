// Robovac dashboard: draws the stored map + live robot pose, sends commands.
const canvas = document.getElementById("map");
const ctx = canvas.getContext("2d");
const statusEl = document.getElementById("status");
const coverageEl = document.getElementById("coverage");

// Draw the latest stored map underneath the live robot dot.
const mapImg = new Image();
mapImg.onload = () => ctx.drawImage(mapImg, 0, 0, canvas.width, canvas.height);
mapImg.src = "/maps/house.png?" + Date.now(); // cache-bust

// TODO(M5): translate world meters -> canvas pixels using map metadata.
function drawRobot(pose) {
  const px = pose.x * 50 + canvas.width / 2;
  const py = canvas.height / 2 - pose.y * 50;
  ctx.fillStyle = "#e63946";
  ctx.beginPath();
  ctx.arc(px, py, 6, 0, Math.PI * 2);
  ctx.fill();
}

// Live telemetry over the server's WebSocket bridge.
const ws = new WebSocket(`ws://${location.host}/ws`);
ws.onopen = () => (statusEl.textContent = "connected");
ws.onclose = () => (statusEl.textContent = "disconnected");
ws.onmessage = (ev) => {
  const msg = JSON.parse(ev.data);
  if (msg.pose) drawRobot(msg.pose);
  if (msg.coverage_pct != null)
    coverageEl.textContent = `Coverage: ${msg.coverage_pct.toFixed(0)}%`;
};

// Command buttons -> POST /commands
document.querySelectorAll("button[data-cmd]").forEach((btn) =>
  btn.addEventListener("click", () =>
    fetch("/commands", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: btn.dataset.cmd }),
    })
  )
);
