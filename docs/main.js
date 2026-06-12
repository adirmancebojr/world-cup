import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const $ = (s) => document.querySelector(s);
const pct = (p, d = 1) => (p * 100).toFixed(d) + "%";

const data = await fetch("./data/site_data.json").then((r) => r.json());
$("#updated").textContent = `results through ${data.results_through ?? "—"} · model run ${data.generated_utc}`;

/* ---------------- 3D probability skyline ---------------- */
const canvas = $("#scene");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0e1a);
scene.fog = new THREE.Fog(0x0a0e1a, 60, 150);

const camera = new THREE.PerspectiveCamera(42, 2, 0.1, 300);
camera.position.set(0, 30, 52);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.6;
controls.maxPolarAngle = Math.PI * 0.47;
controls.minDistance = 18;
controls.maxDistance = 95;
controls.target.set(0, 4, 0);

scene.add(new THREE.AmbientLight(0x6677aa, 0.55));
const key = new THREE.DirectionalLight(0xfff3d6, 1.5);
key.position.set(30, 45, 20);
scene.add(key);
const rim = new THREE.DirectionalLight(0x2dd4bf, 0.8);
rim.position.set(-35, 25, -30);
scene.add(rim);

const ground = new THREE.Mesh(
  new THREE.CircleGeometry(95, 64),
  new THREE.MeshStandardMaterial({ color: 0x0d1326, metalness: 0.75, roughness: 0.45 })
);
ground.rotation.x = -Math.PI / 2;
scene.add(ground);
const grid = new THREE.GridHelper(190, 60, 0x1f2a4a, 0x141d38);
grid.position.y = 0.01;
scene.add(grid);

function textSprite(text, { size = 56, color = "#e7ecf5", bold = 800 } = {}) {
  const c = document.createElement("canvas");
  const ctx = c.getContext("2d");
  ctx.font = `${bold} ${size}px ui-sans-serif, system-ui`;
  c.width = Math.ceil(ctx.measureText(text).width) + 16;
  c.height = size + 18;
  const ctx2 = c.getContext("2d");
  ctx2.font = `${bold} ${size}px ui-sans-serif, system-ui`;
  ctx2.fillStyle = color;
  ctx2.textBaseline = "top";
  ctx2.fillText(text, 8, 6);
  const tex = new THREE.CanvasTexture(c);
  tex.anisotropy = 4;
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false }));
  sp.scale.set(c.width / 38, c.height / 38, 1);
  return sp;
}

const colLow = new THREE.Color(0x274868);
const colMid = new THREE.Color(0x2dd4bf);
const colHot = new THREE.Color(0xfbbf24);
function probColor(p) {
  const t = Math.min(1, Math.sqrt(p) / Math.sqrt(0.2));
  return t < 0.55 ? colLow.clone().lerp(colMid, t / 0.55) : colMid.clone().lerp(colHot, (t - 0.55) / 0.45);
}

const letters = Object.keys(data.groups).sort();
const pickables = [];
const GX = 16, GZ = 15, IN = 3.4;
letters.forEach((g, gi) => {
  const cx = (gi % 4 - 1.5) * GX;
  const cz = (Math.floor(gi / 4) - 1) * GZ;
  const gl = textSprite(`GROUP ${g}`, { size: 40, color: "#5e6f95", bold: 700 });
  gl.position.set(cx, 0.6, cz + IN + 2.6);
  scene.add(gl);
  data.teams.filter((t) => t.group === `Group ${g}` || t.group === g).forEach((t, ti) => {
    const h = 1 + 46 * Math.pow(t.p_champion, 0.62);
    const geo = new THREE.BoxGeometry(2.1, h, 2.1);
    const mat = new THREE.MeshStandardMaterial({
      color: probColor(t.p_champion),
      emissive: probColor(t.p_champion),
      emissiveIntensity: 0.22,
      metalness: 0.35,
      roughness: 0.35,
    });
    const box = new THREE.Mesh(geo, mat);
    box.position.set(cx + (ti % 2 - 0.5) * IN, h / 2, cz + (Math.floor(ti / 2) - 0.5) * IN);
    box.userData.team = t;
    scene.add(box);
    pickables.push(box);
    const lbl = textSprite(t.code, { size: 44 });
    lbl.position.set(box.position.x, h + 1.6, box.position.z);
    scene.add(lbl);
  });
});

const ray = new THREE.Raycaster();
const mouse = new THREE.Vector2();
const tooltip = $("#tooltip");
let hovered = null;
canvas.addEventListener("pointermove", (e) => {
  const r = canvas.getBoundingClientRect();
  mouse.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(mouse, camera);
  const hit = ray.intersectObjects(pickables)[0];
  if (hovered) hovered.material.emissiveIntensity = 0.22;
  if (hit) {
    hovered = hit.object;
    hovered.material.emissiveIntensity = 0.65;
    const t = hovered.userData.team;
    tooltip.innerHTML = `<span class="tt-name">${t.name}</span> · <span class="tt-prob">${pct(t.p_champion)}</span> champion<br>
      <span style="color:var(--dim)">advance ${pct(t.p_r32, 0)} · Elo ${t.elo} (#${t.elo_rank})</span>`;
    tooltip.style.left = e.clientX - r.left + 14 + "px";
    tooltip.style.top = e.clientY - r.top + 10 + "px";
    tooltip.hidden = false;
    canvas.style.cursor = "pointer";
  } else {
    hovered = null;
    tooltip.hidden = true;
    canvas.style.cursor = "grab";
  }
});
canvas.addEventListener("click", () => {
  if (!hovered) return;
  const t = hovered.userData.team;
  $("#panel-name").textContent = t.name;
  $("#panel-sub").textContent = `${t.group} · Elo ${t.elo} (world #${t.elo_rank}) · ${t.pts} pts from ${t.played} played`;
  const rows = [["Round of 32", t.p_r32], ["Round of 16", t.p_r16], ["Quarter-final", t.p_qf], ["Semi-final", t.p_sf], ["Final", t.p_final], ["Champion", t.p_champion]];
  $("#panel-ladder").innerHTML = rows.map(([l, p]) =>
    `<div class="ladder-row"><span class="lbl">${l}</span><span class="bar"><i style="width:${Math.max(1.5, p * 100)}%"></i></span><span class="val">${pct(p)}</span></div>`).join("");
  $("#team-panel").hidden = false;
});
$("#panel-close").onclick = () => ($("#team-panel").hidden = true);
canvas.addEventListener("pointerdown", () => (controls.autoRotate = false), { once: true });

function resize() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(canvas);
renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });

/* ---------------- DOM sections ---------------- */
const byChamp = [...data.teams].sort((a, b) => b.p_champion - a.p_champion);
$("#odds-list").innerHTML = byChamp.slice(0, 12).map((t, i) =>
  `<div class="odds-row"><span class="rank">${i + 1}</span><span class="code" title="${t.name}">${t.code}</span>
   <span class="bar"><i style="width:${(t.p_champion / byChamp[0].p_champion) * 100}%"></i></span>
   <span class="val">${pct(t.p_champion)}</span></div>`).join("");

const played = data.matches.filter((m) => m.status === "played").reverse();
const upcoming = data.matches.filter((m) => m.status === "upcoming").slice(0, 13 - Math.min(4, played.length));
const matchCard = (m) => {
  const head = `<div class="m-head"><span>${m.group ?? ""} · ${m.ground ?? ""}</span><span>${m.date}</span></div>`;
  if (m.status === "played")
    return `<div class="match">${head}<div class="m-teams"><span>${m.home}</span><span class="m-score">${m.hs}–${m.as_}</span><span>${m.away}</span></div></div>`;
  const exp = m.exp_scores ? `<div class="exp-scores"><em>EXPERIMENTAL</em>likely scores: ${m.exp_scores}</div>` : "";
  return `<div class="match">${head}
    <div class="m-teams"><span>${m.home}</span><span style="color:var(--dim)">vs</span><span>${m.away}</span></div>
    <div class="probbar"><span class="ph" style="width:${m.p_home * 100}%"></span><span class="pd" style="width:${m.p_draw * 100}%"></span><span class="pa" style="width:${m.p_away * 100}%"></span></div>
    <div class="probpct"><span>${pct(m.p_home, 0)}</span><span>draw ${pct(m.p_draw, 0)}</span><span>${pct(m.p_away, 0)}</span></div>${exp}</div>`;
};
$("#match-list").innerHTML = played.slice(0, 4).map(matchCard).join("") + upcoming.map(matchCard).join("");

const tmap = Object.fromEntries(data.teams.map((t) => [t.name, t]));
$("#group-grid").innerHTML = letters.map((g) => {
  const names = data.groups[g];
  const rows = names.map((n) => {
    const t = tmap[n];
    return `<tr><td title="${t.name}">${t.code}</td><td>${t.played}</td><td>${t.pts}</td><td>${t.gf - t.ga}</td><td class="adv">${pct(t.p_r32, 0)}</td></tr>`;
  }).join("");
  return `<div class="group-card"><h3>GROUP ${g}</h3><table><tr><th>team</th><th>P</th><th>pts</th><th>GD</th><th>adv</th></tr>${rows}</table></div>`;
}).join("");

$("#scorer-list").innerHTML = data.scorers.map((s) =>
  `<li>${s.name} <span class="s-goals">${s.goals}</span> <span class="s-team">${s.team}</span></li>`).join("");
