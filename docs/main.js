import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import earcut from "./vendor/earcut.mjs";

const $ = (s) => document.querySelector(s);
const pct = (p, d = 1) => (p * 100).toFixed(d) + "%";
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const [data, geo, history] = await Promise.all([
  fetch("./data/site_data.json", { cache: "no-store" }).then((r) => r.json()),
  fetch("./data/countries-110m.geojson").then((r) => r.json()),
  fetch("./data/champion_history.json", { cache: "no-store" }).then((r) => r.ok ? r.json() : null).catch(() => null),
]);
$("#updated").textContent = `results through ${data.results_through ?? "—"} · model run ${data.generated_utc}`;

/* ============== THE EXTRUDED WORLD ==============
   Shaded paper globe, all country outlines as ink map-lines; the 48
   participants raised by title odds and skinned with their flags. */

const R = 16;
const INK = 0x2b2a27;
const maxP = Math.max(...data.teams.map((t) => t.p_champion));
const heightFor = (p) => R * (0.015 + 0.30 * Math.sqrt(p / maxP));
const sideColor = 0xd8d2c4;
const hoverBoost = 0.26;

const flagCache = new Map();
const flagSize = (ctx) => [ctx.canvas.width, ctx.canvas.height];
const paint = (ctx, color) => {
  const [w, h] = flagSize(ctx);
  ctx.fillStyle = color;
  ctx.fillRect(0, 0, w, h);
};
function hStripes(ctx, colors, ratios = colors.map(() => 1)) {
  const [w, h] = flagSize(ctx);
  const total = ratios.reduce((a, b) => a + b, 0);
  let y = 0;
  colors.forEach((color, i) => {
    const hh = i === colors.length - 1 ? h - y : h * ratios[i] / total;
    ctx.fillStyle = color;
    ctx.fillRect(0, y, w, hh);
    y += hh;
  });
}
function vStripes(ctx, colors, ratios = colors.map(() => 1)) {
  const [w, h] = flagSize(ctx);
  const total = ratios.reduce((a, b) => a + b, 0);
  let x = 0;
  colors.forEach((color, i) => {
    const ww = i === colors.length - 1 ? w - x : w * ratios[i] / total;
    ctx.fillStyle = color;
    ctx.fillRect(x, 0, ww, h);
    x += ww;
  });
}
function starPath(ctx, x, y, outer, points = 5, inner = outer * 0.42, rot = -Math.PI / 2) {
  ctx.beginPath();
  for (let i = 0; i < points * 2; i++) {
    const r = i % 2 ? inner : outer;
    const a = rot + i * Math.PI / points;
    const px = x + Math.cos(a) * r;
    const py = y + Math.sin(a) * r;
    if (i) ctx.lineTo(px, py);
    else ctx.moveTo(px, py);
  }
  ctx.closePath();
}
function star(ctx, x, y, outer, color, points = 5, inner = outer * 0.42, rot = -Math.PI / 2) {
  starPath(ctx, x, y, outer, points, inner, rot);
  ctx.fillStyle = color;
  ctx.fill();
}
function circle(ctx, x, y, r, color) {
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.fill();
}
function diamond(ctx, color, padX, padY) {
  const [w, h] = flagSize(ctx);
  ctx.beginPath();
  ctx.moveTo(w / 2, padY);
  ctx.lineTo(w - padX, h / 2);
  ctx.lineTo(w / 2, h - padY);
  ctx.lineTo(padX, h / 2);
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
}
function crescent(ctx, x, y, r, color, cutColor, dx = r * 0.42) {
  circle(ctx, x, y, r, color);
  circle(ctx, x + dx, y - r * 0.04, r * 0.82, cutColor);
}
function stripeLine(ctx, color, width, x1, y1, x2, y2) {
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.lineCap = "butt";
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
}
function triangle(ctx, color, points) {
  ctx.beginPath();
  ctx.moveTo(points[0][0], points[0][1]);
  for (const p of points.slice(1)) ctx.lineTo(p[0], p[1]);
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
}
function cross(ctx, base, color, wRatio = 0.18, hRatio = 0.18, xRatio = 0.5, yRatio = 0.5) {
  paint(ctx, base);
  const [w, h] = flagSize(ctx);
  ctx.fillStyle = color;
  ctx.fillRect(w * xRatio - w * wRatio / 2, 0, w * wRatio, h);
  ctx.fillRect(0, h * yRatio - h * hRatio / 2, w, h * hRatio);
}
function nordic(ctx, base, crossColor, borderColor = null) {
  paint(ctx, base);
  const [w, h] = flagSize(ctx);
  const x = w * 0.36;
  if (borderColor) {
    ctx.fillStyle = borderColor;
    ctx.fillRect(x - w * 0.085, 0, w * 0.17, h);
    ctx.fillRect(0, h * 0.5 - h * 0.12, w, h * 0.24);
  }
  ctx.fillStyle = crossColor;
  ctx.fillRect(x - w * 0.05, 0, w * 0.10, h);
  ctx.fillRect(0, h * 0.5 - h * 0.07, w, h * 0.14);
}
function drawUnionJack(ctx, x, y, w, h) {
  ctx.save();
  ctx.beginPath();
  ctx.rect(x, y, w, h);
  ctx.clip();
  ctx.fillStyle = "#012169";
  ctx.fillRect(x, y, w, h);
  stripeLine(ctx, "#fff", h * 0.22, x, y, x + w, y + h);
  stripeLine(ctx, "#fff", h * 0.22, x + w, y, x, y + h);
  stripeLine(ctx, "#c8102e", h * 0.09, x, y, x + w, y + h);
  stripeLine(ctx, "#c8102e", h * 0.09, x + w, y, x, y + h);
  ctx.fillStyle = "#fff";
  ctx.fillRect(x + w * 0.42, y, w * 0.16, h);
  ctx.fillRect(x, y + h * 0.40, w, h * 0.20);
  ctx.fillStyle = "#c8102e";
  ctx.fillRect(x + w * 0.46, y, w * 0.08, h);
  ctx.fillRect(x, y + h * 0.45, w, h * 0.10);
  ctx.restore();
}
function checker(ctx, x, y, size, colors = ["#f00", "#fff"]) {
  for (let row = 0; row < 5; row++) {
    for (let col = 0; col < 5; col++) {
      ctx.fillStyle = colors[(row + col) % 2];
      ctx.fillRect(x + col * size, y + row * size, size, size);
    }
  }
}
function mapleLeaf(ctx, x, y, s, color) {
  ctx.beginPath();
  const pts = [[0,-1],[-.14,-.48],[-.43,-.62],[-.3,-.25],[-.64,-.18],[-.28,.02],[-.45,.42],[-.1,.28],[0,.78],[.1,.28],[.45,.42],[.28,.02],[.64,-.18],[.3,-.25],[.43,-.62],[.14,-.48]];
  pts.forEach(([px, py], i) => {
    const xx = x + px * s, yy = y + py * s;
    if (i) ctx.lineTo(xx, yy);
    else ctx.moveTo(xx, yy);
  });
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
}
function drawFlag(ctx, code) {
  const [w, h] = flagSize(ctx);
  switch (code) {
    case "ALG": vStripes(ctx, ["#006233", "#fff"]); crescent(ctx, w * .55, h * .50, h * .20, "#d21034", "#fff"); star(ctx, w * .62, h * .50, h * .08, "#d21034"); break;
    case "ARG": hStripes(ctx, ["#74acdf", "#fff", "#74acdf"]); circle(ctx, w * .5, h * .5, h * .085, "#f6b40e"); break;
    case "AUS": paint(ctx, "#00008b"); drawUnionJack(ctx, 0, 0, w * .47, h * .48); star(ctx, w * .25, h * .72, h * .12, "#fff", 7); [[.72,.30],[.82,.47],[.68,.62],[.86,.74]].forEach(([x,y]) => star(ctx, w*x, h*y, h*.055, "#fff", 7)); break;
    case "AUT": hStripes(ctx, ["#ed2939", "#fff", "#ed2939"]); break;
    case "BEL": vStripes(ctx, ["#000", "#ffd90c", "#ef3340"]); break;
    case "BIH": paint(ctx, "#002f6c"); triangle(ctx, "#fcd116", [[w*.46,0],[w,0],[w, h]]); for (let i=0;i<7;i++) star(ctx, w*(.46+i*.075), h*(.10+i*.13), h*.05, "#fff"); break;
    case "BRA": paint(ctx, "#009b3a"); diamond(ctx, "#ffdf00", w * .14, h * .10); circle(ctx, w * .5, h * .5, h * .22, "#002776"); stripeLine(ctx, "#fff", h * .055, w * .30, h * .45, w * .70, h * .57); break;
    case "CAN": vStripes(ctx, ["#d52b1e", "#fff", "#d52b1e"], [1,2,1]); mapleLeaf(ctx, w * .5, h * .52, h * .25, "#d52b1e"); break;
    case "CIV": vStripes(ctx, ["#f77f00", "#fff", "#009e60"]); break;
    case "COD": paint(ctx, "#00a3e0"); stripeLine(ctx, "#f7d618", h * .28, w * -.06, h * 1.05, w * 1.06, h * -.05); stripeLine(ctx, "#ce1021", h * .18, w * -.04, h * 1.04, w * 1.04, h * -.04); star(ctx, w * .22, h * .25, h * .10, "#f7d618"); break;
    case "COL": hStripes(ctx, ["#fcd116", "#003893", "#ce1126"], [2,1,1]); break;
    case "CPV": hStripes(ctx, ["#003893", "#003893", "#fff", "#cf2027", "#fff", "#003893"], [6,3,1,1,1,4]); for (let i=0;i<10;i++) { const a=-Math.PI/2+i*Math.PI*2/10; star(ctx, w*.32+Math.cos(a)*h*.18, h*.56+Math.sin(a)*h*.18, h*.035, "#f7d116"); } break;
    case "CRO": hStripes(ctx, ["#ff0000", "#fff", "#171796"]); checker(ctx, w * .44, h * .33, h * .045); break;
    case "CUW": paint(ctx, "#002b7f"); ctx.fillStyle = "#f9e300"; ctx.fillRect(0, h*.62, w, h*.12); star(ctx, w*.24, h*.28, h*.085, "#fff"); star(ctx, w*.35, h*.18, h*.055, "#fff"); break;
    case "CZE": hStripes(ctx, ["#fff", "#d7141a"]); triangle(ctx, "#11457e", [[0,0],[w*.48,h*.5],[0,h]]); break;
    case "ECU": hStripes(ctx, ["#ffdd00", "#034ea2", "#ed1c24"], [2,1,1]); circle(ctx, w*.5, h*.5, h*.08, "#8a6116"); break;
    case "EGY": hStripes(ctx, ["#ce1126", "#fff", "#000"]); circle(ctx, w*.5, h*.5, h*.06, "#c09300"); break;
    case "ENG": cross(ctx, "#fff", "#cf142b", .13, .18); break;
    case "ESP": hStripes(ctx, ["#aa151b", "#f1bf00", "#aa151b"], [1,2,1]); circle(ctx, w*.38, h*.5, h*.06, "#7a4a16"); break;
    case "FRA": vStripes(ctx, ["#0055a4", "#fff", "#ef4135"]); break;
    case "GER": hStripes(ctx, ["#000", "#dd0000", "#ffce00"]); break;
    case "GHA": hStripes(ctx, ["#ce1126", "#fcd116", "#006b3f"]); star(ctx, w*.5, h*.5, h*.11, "#000"); break;
    case "HAI": hStripes(ctx, ["#00209f", "#d21034"]); ctx.fillStyle = "#fff"; ctx.fillRect(w*.40, h*.37, w*.20, h*.26); break;
    case "IRN": hStripes(ctx, ["#239f40", "#fff", "#da0000"]); circle(ctx, w*.5, h*.5, h*.07, "#da0000"); break;
    case "IRQ": hStripes(ctx, ["#ce1126", "#fff", "#000"]); ctx.fillStyle = "#007a3d"; ctx.font = `900 ${h*.18}px ${getComputedStyle(document.body).fontFamily}`; ctx.textAlign = "center"; ctx.fillText("الله", w*.5, h*.56); break;
    case "JOR": hStripes(ctx, ["#000", "#fff", "#007a3d"]); triangle(ctx, "#ce1126", [[0,0],[w*.45,h*.5],[0,h]]); star(ctx, w*.18, h*.5, h*.055, "#fff", 7); break;
    case "JPN": paint(ctx, "#fff"); circle(ctx, w*.5, h*.5, h*.20, "#bc002d"); break;
    case "KOR": paint(ctx, "#fff"); circle(ctx, w*.5, h*.5, h*.18, "#cd2e3a"); ctx.beginPath(); ctx.arc(w*.5, h*.5, h*.18, 0, Math.PI); ctx.fillStyle = "#0047a0"; ctx.fill(); stripeLine(ctx, "#000", h*.025, w*.20, h*.24, w*.32, h*.34); stripeLine(ctx, "#000", h*.025, w*.68, h*.66, w*.80, h*.76); break;
    case "KSA": paint(ctx, "#006c35"); ctx.fillStyle = "#fff"; ctx.font = `700 ${h*.15}px ${getComputedStyle(document.body).fontFamily}`; ctx.textAlign = "center"; ctx.fillText("لا إله إلا الله", w*.5, h*.43); stripeLine(ctx, "#fff", h*.035, w*.30, h*.68, w*.72, h*.68); break;
    case "MAR": paint(ctx, "#c1272d"); star(ctx, w*.5, h*.5, h*.17, "#006233", 5, h*.065); break;
    case "MEX": vStripes(ctx, ["#006847", "#fff", "#ce1126"]); circle(ctx, w*.5, h*.5, h*.075, "#8c6b2f"); break;
    case "NED": hStripes(ctx, ["#ae1c28", "#fff", "#21468b"]); break;
    case "NOR": nordic(ctx, "#ba0c2f", "#00205b", "#fff"); break;
    case "NZL": paint(ctx, "#00247d"); drawUnionJack(ctx, 0, 0, w*.48, h*.48); [[.70,.32],[.82,.48],[.70,.66],[.86,.73]].forEach(([x,y]) => { star(ctx, w*x, h*y, h*.065, "#fff"); star(ctx, w*x, h*y, h*.045, "#cc142b"); }); break;
    case "PAN": paint(ctx, "#fff"); ctx.fillStyle = "#d21034"; ctx.fillRect(w*.5, 0, w*.5, h*.5); ctx.fillStyle = "#005293"; ctx.fillRect(0, h*.5, w*.5, h*.5); star(ctx, w*.25, h*.25, h*.07, "#005293"); star(ctx, w*.75, h*.75, h*.07, "#d21034"); break;
    case "PAR": hStripes(ctx, ["#d52b1e", "#fff", "#0038a8"]); circle(ctx, w*.5, h*.5, h*.075, "#f4c430"); break;
    case "POR": vStripes(ctx, ["#006600", "#ff0000"], [2,3]); circle(ctx, w*.40, h*.5, h*.09, "#ffcc00"); break;
    case "QAT": paint(ctx, "#8a1538"); ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.moveTo(0,0); for (let i=0;i<9;i++) { ctx.lineTo(w*.24, h*(i+.5)/9); ctx.lineTo(0, h*(i+1)/9); } ctx.lineTo(0,0); ctx.fill(); break;
    case "RSA": paint(ctx, "#de3831"); ctx.fillStyle = "#002395"; ctx.fillRect(0,h*.5,w,h*.5); triangle(ctx, "#000", [[0,0],[w*.42,h*.5],[0,h]]); triangle(ctx, "#ffb612", [[0,h*.08],[w*.36,h*.5],[0,h*.92]]); stripeLine(ctx, "#fff", h*.18, w*.05, h*.02, w*.48, h*.5); stripeLine(ctx, "#fff", h*.18, w*.05, h*.98, w*.48, h*.5); stripeLine(ctx, "#007a4d", h*.12, w*.08, h*.07, w*.52, h*.5); stripeLine(ctx, "#007a4d", h*.12, w*.08, h*.93, w*.52, h*.5); ctx.fillStyle="#007a4d"; ctx.fillRect(w*.36,h*.44,w*.64,h*.12); break;
    case "SCO": paint(ctx, "#0065bd"); stripeLine(ctx, "#fff", h*.16, 0, 0, w, h); stripeLine(ctx, "#fff", h*.16, w, 0, 0, h); break;
    case "SEN": vStripes(ctx, ["#00853f", "#fdef42", "#e31b23"]); star(ctx, w*.5, h*.5, h*.09, "#00853f"); break;
    case "SUI": paint(ctx, "#d52b1e"); ctx.fillStyle="#fff"; ctx.fillRect(w*.43,h*.23,w*.14,h*.54); ctx.fillRect(w*.28,h*.40,w*.44,h*.20); break;
    case "SWE": nordic(ctx, "#006aa7", "#fecc00"); break;
    case "TUN": paint(ctx, "#e70013"); circle(ctx, w*.5, h*.5, h*.22, "#fff"); crescent(ctx, w*.48, h*.5, h*.10, "#e70013", "#fff", h*.045); star(ctx, w*.56, h*.5, h*.065, "#e70013"); break;
    case "TUR": paint(ctx, "#e30a17"); crescent(ctx, w*.43, h*.5, h*.20, "#fff", "#e30a17", h*.08); star(ctx, w*.58, h*.5, h*.075, "#fff"); break;
    case "URU": hStripes(ctx, ["#fff","#0038a8","#fff","#0038a8","#fff","#0038a8","#fff","#0038a8","#fff"]); ctx.fillStyle="#fff"; ctx.fillRect(0,0,w*.42,h*.50); circle(ctx, w*.20,h*.25,h*.08,"#fcd116"); break;
    case "USA": hStripes(ctx, Array.from({ length: 13 }, (_, i) => i % 2 ? "#fff" : "#b22234")); ctx.fillStyle="#3c3b6e"; ctx.fillRect(0,0,w*.42,h*7/13); for (let r=0;r<5;r++) for (let c=0;c<6;c++) star(ctx, w*(.045+c*.06), h*(.055+r*.08), h*.018, "#fff"); break;
    case "UZB": hStripes(ctx, ["#0099b5","#ce1126","#fff","#ce1126","#1eb53a"], [5, .25, 4.5, .25, 5]); crescent(ctx, w*.18,h*.21,h*.075,"#fff","#0099b5",h*.035); for (let i=0;i<6;i++) star(ctx, w*(.30+i*.045), h*.16, h*.020, "#fff"); break;
    default:
      hStripes(ctx, ["#88b7e6", "#fff", "#d98a6a"]);
      ctx.fillStyle = "#2b2a27";
      ctx.font = `800 ${h * .28}px 'IBM Plex Mono','SF Mono',Menlo,monospace`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(code, w / 2, h / 2);
  }
}
// FIFA code -> flag-icons file (ISO 3166-1 alpha-2; UK nations use gb-*)
const FLAG_CODE = {
  ESP: "es", ARG: "ar", FRA: "fr", ENG: "gb-eng", BRA: "br", COL: "co", POR: "pt", ECU: "ec",
  NED: "nl", MEX: "mx", GER: "de", JPN: "jp", MAR: "ma", TUR: "tr", URU: "uy", BEL: "be",
  NOR: "no", SUI: "ch", CRO: "hr", USA: "us", KOR: "kr", PAR: "py", SEN: "sn", IRN: "ir",
  AUS: "au", CAN: "ca", AUT: "at", ALG: "dz", PAN: "pa", SCO: "gb-sct", UZB: "uz", CIV: "ci",
  EGY: "eg", JOR: "jo", NZL: "nz", SWE: "se", COD: "cd", CZE: "cz", TUN: "tn", IRQ: "iq",
  HAI: "ht", KSA: "sa", RSA: "za", GHA: "gh", CPV: "cv", BIH: "ba", QAT: "qa", CUW: "cw",
};
function flagTexture(team) {
  const key = team.code;
  if (flagCache.has(key)) return flagCache.get(key);
  const c = document.createElement("canvas");
  c.width = 512;
  c.height = 384; // 4:3, matching flag-icons source
  const ctx = c.getContext("2d");
  drawFlag(ctx, team.code); // fallback shown while the SVG loads / if it fails

  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  flagCache.set(key, tex);

  const file = FLAG_CODE[team.code];
  if (file) {
    const img = new Image();
    img.onload = () => {
      ctx.clearRect(0, 0, c.width, c.height);
      ctx.drawImage(img, 0, 0, c.width, c.height);
      tex.needsUpdate = true;
    };
    img.onerror = () => console.warn("flag failed, using fallback:", team.code);
    img.src = `./flags/4x3/${file}.svg`;
  }
  return tex;
}
function flagMaterials(team) {
  const map = flagTexture(team);
  const top = new THREE.MeshStandardMaterial({
    map, color: 0xffffff, emissive: 0xffffff, emissiveMap: map, emissiveIntensity: 0.08,
    roughness: 0.7, metalness: 0.02, side: THREE.DoubleSide,
  });
  top.userData.baseEmissive = 0.08;
  const side = new THREE.MeshStandardMaterial({
    color: sideColor, emissive: sideColor, emissiveIntensity: 0.0,
    roughness: 0.68, metalness: 0.04, side: THREE.DoubleSide,
  });
  side.userData.baseEmissive = 0.0;
  return [top, side];
}
function pinMaterials(team) {
  const [top, side] = flagMaterials(team);
  return [side, top, side];
}
function setGlow(obj, boost) {
  const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
  for (const mat of mats) {
    if ("emissiveIntensity" in mat) mat.emissiveIntensity = (mat.userData.baseEmissive ?? 0) + boost;
  }
}

function llv(lat, lng, r = R) {
  const phi = (90 - lat) * Math.PI / 180;
  const theta = (lng + 180) * Math.PI / 180;
  return new THREE.Vector3(
    -r * Math.sin(phi) * Math.cos(theta),
    r * Math.cos(phi),
    r * Math.sin(phi) * Math.sin(theta)
  );
}

// representative lat/lng for teams whose polygon is missing in 110m
const PIN_COORDS = {
  "Scotland": [56.5, -4.2], "Cape Verde": [16.0, -24.0], "Curaçao": [12.2, -69.0], "Curacao": [12.2, -69.0],
};
// team name -> acceptable Natural Earth name strings
const ALIASES = {
  "United States": ["United States of America", "United States"],
  "England": ["United Kingdom"],
  "DR Congo": ["Dem. Rep. Congo", "Democratic Republic of the Congo"],
  "Czech Republic": ["Czechia", "Czech Rep.", "Czech Republic"],
  "Ivory Coast": ["Côte d'Ivoire", "Ivory Coast"],
  "South Korea": ["South Korea", "Republic of Korea"],
  "Turkey": ["Turkey", "Türkiye", "Turkiye"],
  "Bosnia and Herzegovina": ["Bosnia and Herz.", "Bosnia and Herzegovina"],
  "Iran": ["Iran", "Iran (Islamic Republic of)"],
};
const teamByName = Object.fromEntries(data.teams.map((t) => [t.name, t]));
// build NE-name -> team lookup
const neToTeam = {};
for (const t of data.teams) {
  neToTeam[t.name] = t;
  for (const a of ALIASES[t.name] ?? []) neToTeam[a] = t;
}
// match only on specific name fields — NOT SOVEREIGNT/BRK_NAME, which would
// grab overseas territories (Falklands→England, Fr. S. Antarctic→France).
const NEFIELDS = ["NAME", "ADMIN", "NAME_LONG", "NAME_EN", "GEOUNIT"];
function featureMatchesTeam(f, teamName) {
  for (const k of NEFIELDS) { const v = f.properties[k]; if (v && neToTeam[v]?.name === teamName) return true; }
  return false;
}

const canvas = $("#scene");
let renderer;
try {
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
} catch (e) {
  // no WebGL (some sandboxes/old browsers): hide the globe, keep the data views
  console.warn("WebGL unavailable — globe disabled, rest of the page still renders", e);
  document.querySelector("#scene-wrap")?.style.setProperty("display", "none");
  renderer = { setPixelRatio() {}, setSize() {}, render() {}, setAnimationLoop() {}, domElement: canvas };
}
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(42, 2, 0.1, 300);
camera.position.set(0, 6, 56);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.enablePan = false;
controls.minDistance = 30;
controls.maxDistance = 90;

scene.add(new THREE.AmbientLight(0xffffff, 0.84));
const key = new THREE.DirectionalLight(0xffffff, 0.85);
key.position.set(40, 55, 35);
scene.add(key);
const fill = new THREE.DirectionalLight(0xdfe7f1, 0.3);
fill.position.set(-35, 12, -25);
scene.add(fill);

const tilt = new THREE.Group();
tilt.rotation.z = 0.12;
tilt.rotation.x = 0.34; // tip north pole toward the viewer so Europe sits centre-frame
scene.add(tilt);
const globe = new THREE.Group();
globe.rotation.y = -1.5; // open on Europe — Spain (tallest, #1) front and centre
tilt.add(globe);

// invisible occluder: painted the exact page background and unlit, so the
// globe reads as transparent while still hiding the far side (clean front).
globe.add(new THREE.Mesh(
  new THREE.SphereGeometry(R * 0.99, 64, 48),
  new THREE.MeshBasicMaterial({ color: 0xfaf9f6 })
));

// --- helpers on rings ([lng,lat] arrays) ---
const ringArea = (ring) => {
  let a = 0;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++)
    a += (ring[j][0] - ring[i][0]) * (ring[j][1] + ring[i][1]);
  return Math.abs(a / 2);
};
const totalArea = (geom) => polygonsOf(geom).reduce((s, poly) => s + ringArea(poly[0]), 0);
function polygonsOf(geom) {
  return geom.type === "Polygon" ? [geom.coordinates] : geom.coordinates; // -> [ [ring,...], ... ]
}

// all borders as ink map-lines
const borderMat = new THREE.LineBasicMaterial({ color: INK, transparent: true, opacity: 0.3 });
for (const f of geo.features) {
  for (const poly of polygonsOf(f.geometry)) {
    for (const ring of poly) {
      const pts = ring.map(([lng, lat]) => llv(lat, lng, R * 1.002));
      globe.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), borderMat));
    }
  }
}

// extrude one ring (largest polygon of a country) to height h
function extrudeRing(ring, h, team) {
  let r = ring.slice();
  if (r.length > 1 && r[0][0] === r[r.length - 1][0] && r[0][1] === r[r.length - 1][1]) r.pop();
  if (r.length < 3) return null;
  // earcut is far more robust than ShapeUtils on complex concave rings
  // (e.g. Brazil, 203 pts) — ShapeUtils left holes in the top face.
  const flat = [];
  for (const [lng, lat] of r) flat.push(lng, lat);
  const tri = earcut(flat); // flat list of vertex indices, 3 per triangle
  if (!tri.length) return null;
  const topR = R + h;
  const top = r.map(([lng, lat]) => llv(lat, lng, topR));
  const bot = r.map(([lng, lat]) => llv(lat, lng, R * 1.003));
  const pos = [];
  const uv = [];
  const lngs = r.map(([lng]) => lng), lats = r.map(([, lat]) => lat);
  const minLng = Math.min(...lngs), maxLng = Math.max(...lngs);
  const minLat = Math.min(...lats), maxLat = Math.max(...lats);
  const spanLng = Math.max(0.001, maxLng - minLng);
  const spanLat = Math.max(0.001, maxLat - minLat);
  // push a lng/lat vertex of the top cap, projected onto the sphere
  const pushTopLL = (lng, lat) => {
    const v = llv(lat, lng, topR);
    pos.push(v.x, v.y, v.z);
    uv.push((lng - minLng) / spanLng, (lat - minLat) / spanLat);
  };
  const pushSide = (v, u, vv) => {
    pos.push(v.x, v.y, v.z);
    uv.push(u, vv);
  };
  // tessellate large triangles so the flat cap hugs the sphere — otherwise big
  // countries (Brazil) bow inward between vertices and the occluder pokes
  // through, leaving a "hole" in the middle of the flag.
  const MAX_EDGE = 3; // degrees
  const mid = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  const span = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
  const emitTri = (a, b, c, depth) => {
    if (depth <= 0 || Math.max(span(a, b), span(b, c), span(c, a)) <= MAX_EDGE) {
      pushTopLL(a[0], a[1]); pushTopLL(b[0], b[1]); pushTopLL(c[0], c[1]);
      return;
    }
    const ab = mid(a, b), bc = mid(b, c), ca = mid(c, a);
    emitTri(a, ab, ca, depth - 1); emitTri(ab, b, bc, depth - 1);
    emitTri(ca, bc, c, depth - 1); emitTri(ab, bc, ca, depth - 1);
  };
  for (let k = 0; k < tri.length; k += 3) { // top cap
    emitTri(r[tri[k]], r[tri[k + 1]], r[tri[k + 2]], 5);
  }
  const topCount = pos.length / 3;
  for (let i = 0; i < r.length; i++) { // walls
    const j = (i + 1) % r.length;
    const u0 = i / r.length, u1 = (i + 1) / r.length;
    pushSide(bot[i], u0, 0); pushSide(bot[j], u1, 0); pushSide(top[i], u0, 1);
    pushSide(top[i], u0, 1); pushSide(bot[j], u1, 0); pushSide(top[j], u1, 1);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
  g.addGroup(0, topCount, 0);
  g.addGroup(topCount, pos.length / 3 - topCount, 1);
  g.computeVertexNormals();
  const mesh = new THREE.Mesh(g, flagMaterials(team));
  return mesh;
}

const pickables = [];
const placed = new Set();

// extruded participant countries — for each team pick the largest-area
// matching feature (mainland over any territory), then its largest ring.
for (const t of data.teams) {
  const cands = geo.features.filter((f) => featureMatchesTeam(f, t.name));
  if (!cands.length) continue;
  const feat = cands.reduce((b, f) => (totalArea(f.geometry) > totalArea(b.geometry) ? f : b));
  let best = null, bestA = -1;
  for (const poly of polygonsOf(feat.geometry)) { const a = ringArea(poly[0]); if (a > bestA) { bestA = a; best = poly[0]; } }
  if (!best) continue;
  const h = heightFor(t.p_champion);
  const mesh = extrudeRing(best, h, t);
  if (!mesh) continue;
  mesh.userData.team = t;
  globe.add(mesh);
  pickables.push(mesh);
  placed.add(t.name);
}

// pins for teams with no polygon in 110m
for (const t of data.teams) {
  if (placed.has(t.name)) continue;
  const ll = PIN_COORDS[t.name];
  if (!ll) { console.warn("no polygon or pin for", t.name); continue; }
  const h = heightFor(t.p_champion);
  const dir = llv(ll[0], ll[1], 1).normalize();
  const geoCyl = new THREE.CylinderGeometry(0.32, 0.32, h, 12);
  const mesh = new THREE.Mesh(geoCyl, pinMaterials(t));
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
  mesh.position.copy(dir.clone().multiplyScalar(R + h / 2));
  mesh.userData.team = t;
  globe.add(mesh);
  pickables.push(mesh);
  placed.add(t.name);
}

const ray = new THREE.Raycaster();
const mouse = new THREE.Vector2();
const tooltip = $("#tooltip");
let hovered = null;
const clearHover = () => { if (hovered) { setGlow(hovered, 0); hovered = null; } };
canvas.addEventListener("pointermove", (e) => {
  const r = canvas.getBoundingClientRect();
  mouse.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(mouse, camera);
  const hit = ray.intersectObjects(pickables)[0];
  if (hit && hit.object === hovered) { place(e, r); return; }
  clearHover();
  if (hit) {
    hovered = hit.object;
    setGlow(hovered, hoverBoost);
    const t = hovered.userData.team;
    tooltip.innerHTML = `<span class="tt-name">${t.name}</span> · <span class="tt-prob">${pct(t.p_champion)}</span> champion<br>
      <span style="color:var(--muted)">advance ${pct(t.p_r32, 0)} · Elo ${t.elo} (#${t.elo_rank})</span>`;
    tooltip.hidden = false;
    place(e, r);
    canvas.style.cursor = "pointer";
  } else { tooltip.hidden = true; canvas.style.cursor = "grab"; }
});
function place(e, r) {
  tooltip.style.left = e.clientX - r.left + 14 + "px";
  tooltip.style.top = e.clientY - r.top + 10 + "px";
}
canvas.addEventListener("click", () => {
  if (!hovered) return;
  const t = hovered.userData.team;
  $("#panel-name").textContent = t.name;
  $("#panel-sub").textContent = `Group ${t.group} · Elo ${t.elo} (world #${t.elo_rank}) · ${t.pts} pts from ${t.played} played`;
  const rows = [["Round of 32", t.p_r32], ["Round of 16", t.p_r16], ["Quarter-final", t.p_qf], ["Semi-final", t.p_sf], ["Final", t.p_final], ["Champion", t.p_champion]];
  $("#panel-ladder").innerHTML = rows.map(([l, p]) =>
    `<div class="ladder-row"><span class="lbl">${l}</span><span class="bar"><i style="width:${Math.max(1.5, p * 100)}%"></i></span><span class="val">${pct(p)}</span></div>`).join("");
  $("#team-panel").hidden = false;
});
$("#panel-close").onclick = () => ($("#team-panel").hidden = true);

let spinning = false;
setTimeout(() => (spinning = true), 3800); // hold the opening on Spain, then drift west
canvas.addEventListener("pointerdown", () => (spinning = false));
canvas.addEventListener("pointerup", () => setTimeout(() => (spinning = true), 2500));

function resize() {
  const w = canvas.clientWidth, h = canvas.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(canvas);
renderer.setAnimationLoop(() => {
  if (spinning) globe.rotation.y += 0.0011;
  controls.update();
  renderer.render(scene, camera);
});

/* ---------------- DOM sections ---------------- */
const letters = Object.keys(data.groups).sort();
const tmap = Object.fromEntries(data.teams.map((t) => [t.name, t]));
const matchesById = Object.fromEntries(data.matches.map((m) => [m.id, m]));
const byChamp = [...data.teams].sort((a, b) => b.p_champion - a.p_champion);

// champion odds as an interactive time scrubber (bar-chart race) ----------
const curOdds = Object.fromEntries(data.teams.map((t) => [t.code, t.p_champion]));
const frames = (history?.snapshots ?? []).slice().sort((a, b) => a.matches_played - b.matches_played);
if (!frames.length) frames.push({ t: data.results_through, matches_played: data.matches_played ?? 0, odds: curOdds });
// roster = every team that was in the top 12 on ANY day, so the race keeps teams
// that led early and faded (e.g. Spain), showing each day's true top 12.
const teamByCode = Object.fromEntries(data.teams.map((t) => [t.code, t]));
const rosterCodes = new Set(byChamp.slice(0, 12).map((t) => t.code));
for (const f of frames) Object.entries(f.odds).sort((a, b) => b[1] - a[1]).slice(0, 12).forEach(([c]) => rosterCodes.add(c));
const ROSTER = [...rosterCodes].map((c) => teamByCode[c]).filter(Boolean);
const ROW_H = 34;
const oddsAt = (f, code) => f.odds[code] ?? curOdds[code] ?? 0;
const maxOdds = Math.max(0.02, ...ROSTER.flatMap((t) => frames.map((f) => oddsAt(f, t.code))));
const fmtDay = (iso) => iso ? new Date(iso + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "—";

const TOP_N = 12; // list is capped at 12; teams outside a day's top 12 fade out
const oddsList = $("#odds-list");
oddsList.style.height = Math.min(TOP_N, ROSTER.length) * ROW_H + "px";
oddsList.innerHTML = "";
const rowFor = new Map();
for (const t of ROSTER) {
  const row = document.createElement("div");
  row.className = "odds-row";
  row.innerHTML = `<span class="rank"></span><span class="code" title="${esc(t.name)}">${esc(t.code)}</span><span class="bar"><i></i></span><span class="val"></span>`;
  oddsList.appendChild(row);
  rowFor.set(t.code, { row, rank: row.querySelector(".rank"), bar: row.querySelector("i"), val: row.querySelector(".val") });
}
function renderOddsAt(i) {
  const f = frames[i];
  [...ROSTER].sort((a, b) => oddsAt(f, b.code) - oddsAt(f, a.code)).forEach((t, r) => {
    const ref = rowFor.get(t.code), o = oddsAt(f, t.code);
    const shown = r < TOP_N; // list capped at 12; lower ranks fade out but stay mounted for animation
    ref.row.style.transform = `translateY(${Math.min(r, TOP_N) * ROW_H}px)`;
    ref.row.style.opacity = shown ? "1" : "0";
    ref.row.style.pointerEvents = shown ? "" : "none";
    ref.rank.textContent = r + 1;
    ref.bar.style.width = (o / maxOdds * 100).toFixed(1) + "%";
    ref.val.textContent = pct(o);
  });
  const lbl = $("#odds-time-label");
  if (lbl) lbl.textContent = `through ${fmtDay(f.t)} · ${f.matches_played} match${f.matches_played === 1 ? "" : "es"}`;
}

let cur = frames.length - 1, playing = false, timer = null;
const timeBar = $("#odds-time"), scrub = $("#odds-scrub"), playBtn = $("#odds-play");
if (timeBar && frames.length >= 2) {
  timeBar.hidden = false;
  scrub.max = frames.length - 1;
  scrub.value = cur;
  const setIndex = (i) => { cur = Math.max(0, Math.min(frames.length - 1, i)); scrub.value = cur; renderOddsAt(cur); };
  const stop = () => { playing = false; clearInterval(timer); playBtn.textContent = "▶"; playBtn.setAttribute("aria-label", "play timeline"); };
  $("#odds-prev").onclick = () => { stop(); setIndex(cur - 1); };
  $("#odds-next").onclick = () => { stop(); setIndex(cur + 1); };
  scrub.oninput = () => { stop(); setIndex(+scrub.value); };
  playBtn.onclick = () => {
    if (playing) return stop();
    playing = true; playBtn.textContent = "⏸"; playBtn.setAttribute("aria-label", "pause timeline");
    if (cur >= frames.length - 1) setIndex(0);
    timer = setInterval(() => { cur >= frames.length - 1 ? stop() : setIndex(cur + 1); }, 900);
  };
}
renderOddsAt(cur);
requestAnimationFrame(() => oddsList.classList.add("animate")); // enable transitions after initial layout

const compactDateTime = (() => {
  try {
    return new Intl.DateTimeFormat(undefined, {
      month: "short", day: "numeric", hour: "numeric", minute: "2-digit", timeZoneName: "short",
    });
  } catch {
    return null;
  }
})();
const visitorTime = (() => {
  try {
    return new Intl.DateTimeFormat(undefined, {
      weekday: "short", hour: "numeric", minute: "2-digit", timeZoneName: "short",
    });
  } catch {
    return null;
  }
})();
function matchTime(m) {
  if (visitorTime && m.kickoff_utc) {
    const d = new Date(m.kickoff_utc);
    if (!Number.isNaN(d.valueOf())) return visitorTime.format(d);
  }
  return m.kickoff_local ?? "";
}
const formatDateTime = (iso) => {
  if (!compactDateTime || !iso) return iso ?? "";
  const d = new Date(iso);
  return Number.isNaN(d.valueOf()) ? iso : compactDateTime.format(d);
};
const LIVE_WINDOW_MS = 135 * 60 * 1000;
const scoreFor = (m) => {
  if (m.feed?.status === "played" && Number.isFinite(m.feed.home_score) && Number.isFinite(m.feed.away_score))
    return { home: m.feed.home_score, away: m.feed.away_score, source: "feed" };
  if (m.status === "played" && Number.isFinite(m.hs) && Number.isFinite(m.as_))
    return { home: m.hs, away: m.as_, source: "model" };
  return null;
};
function matchPhase(m) {
  if (scoreFor(m)) return "played";
  const kickoff = Date.parse(m.kickoff_utc ?? "");
  if (!Number.isNaN(kickoff)) {
    const now = Date.now();
    if (now >= kickoff && now <= kickoff + LIVE_WINDOW_MS) return "live";
    if (now > kickoff + LIVE_WINDOW_MS) return "awaiting";
  }
  return "upcoming";
}
function phaseLabel(m) {
  const phase = matchPhase(m);
  if (phase === "played" && m.feed?.status === "played" && m.status !== "played") return "feed final";
  return { played: "final", live: "in progress", awaiting: "awaiting result", upcoming: "scheduled" }[phase];
}
const minuteSort = (minute) => {
  const [base, extra] = String(minute ?? "").split("+");
  return (parseInt(base, 10) || 0) + (parseInt(extra, 10) || 0) / 100;
};
const statRow = (label, value) => value ? `<div class="stat-row"><span>${esc(label)}</span><strong>${value}</strong></div>` : "";
const statRowHtml = (label, value) => value ? `<div class="stat-row"><span>${esc(label)}</span><strong>${value}</strong></div>` : "";
const outcomeText = (m, outcome) => ({ H: `${m.home} win`, D: "draw", A: `${m.away} win` }[outcome] ?? "—");
const outcomeProb = (p, outcome) => ({ H: p?.p_home, D: p?.p_draw, A: p?.p_away }[outcome]);
const hitText = (hit) => hit ? "hit" : "miss";
const predictionMark = (hit) => `<span class="prediction-mark ${hit ? "hit" : "miss"}">${hitText(hit)}</span>`;
const scoreProbText = (p) => typeof p?.top_score_prob === "number" ? ` (${pct(p.top_score_prob, 0)})` : "";
function predictionChips(m) {
  const p = m.prediction;
  if (!p) return "";
  return `<div class="prediction-chips">
    <span class="pred-chip ${p.outcome_hit ? "hit" : "miss"}">outcome ${hitText(p.outcome_hit)}</span>
    <span class="pred-chip ${p.score_hit ? "hit" : "miss"}">score ${hitText(p.score_hit)}</span>
  </div>`;
}
const modelState = (m) => {
  if (m.status === "played") return "incorporated";
  if (scoreFor(m)) return "pending model update";
  return "pre-match";
};

const matchCard = (m) => {
  const timeText = matchTime(m);
  const time = timeText
    ? `<time class="m-time"${m.kickoff_utc ? ` datetime="${esc(m.kickoff_utc)}"` : ""}${m.kickoff_local ? ` title="match local: ${esc(m.kickoff_local)}"` : ""}>${esc(timeText)}</time>`
    : "";
  const head = `<div class="m-head"><span>${esc(m.group ?? m.round ?? "")}</span>${time}</div><div class="m-ground">${esc(m.ground ?? "")}</div>`;
  const phase = matchPhase(m);
  const score = scoreFor(m);
  const href = `#match/${encodeURIComponent(m.id)}`;
  const status = `<span class="match-status ${phase}">${phaseLabel(m)}</span>`;
  if (score)
    return `<a class="match match-link ${phase}" href="${href}" aria-label="Open stats for ${esc(m.home)} vs ${esc(m.away)}">${head}<div class="m-teams"><span>${esc(m.home)}</span><span class="m-score">${score.home}–${score.away}</span><span>${esc(m.away)}</span></div>${predictionChips(m)}${status}</a>`;
  const exp = m.exp_scores ? `<div class="exp-scores"><em>EXPERIMENTAL</em>likely scores: ${esc(m.exp_scores)}</div>` : "";
  return `<a class="match match-link ${phase}" href="${href}" aria-label="Open stats for ${esc(m.home)} vs ${esc(m.away)}">${head}
    <div class="m-teams"><span>${esc(m.home)}</span><span style="color:var(--dim)">vs</span><span>${esc(m.away)}</span></div>
    <div class="probbar"><span class="ph" style="width:${m.p_home * 100}%"></span><span class="pd" style="width:${m.p_draw * 100}%"></span><span class="pa" style="width:${m.p_away * 100}%"></span></div>
    <div class="probpct"><span>${pct(m.p_home, 0)}</span><span>draw ${pct(m.p_draw, 0)}</span><span>${pct(m.p_away, 0)}</span></div>${status}${exp}</a>`;
};

function modelSnapshot(m) {
  if (m.prediction) {
    const p = m.prediction;
    return `<div class="probbar detail-prob"><span class="ph" style="width:${p.p_home * 100}%"></span><span class="pd" style="width:${p.p_draw * 100}%"></span><span class="pa" style="width:${p.p_away * 100}%"></span></div>
      <div class="probpct"><span>${esc(m.home)} ${pct(p.p_home, 0)}</span><span>draw ${pct(p.p_draw, 0)}</span><span>${esc(m.away)} ${pct(p.p_away, 0)}</span></div>
      <div class="exp-scores"><em>PRE-MATCH</em>top score: ${esc(p.top_score)}${scoreProbText(p)}</div>`;
  }
  if (typeof m.p_home !== "number")
    return `<p class="quiet">Current run has already absorbed this result.</p>`;
  const exp = m.exp_scores ? `<div class="exp-scores"><em>EXPERIMENTAL</em>likely scores: ${esc(m.exp_scores)}</div>` : "";
  return `<div class="probbar detail-prob"><span class="ph" style="width:${m.p_home * 100}%"></span><span class="pd" style="width:${m.p_draw * 100}%"></span><span class="pa" style="width:${m.p_away * 100}%"></span></div>
    <div class="probpct"><span>${esc(m.home)} ${pct(m.p_home, 0)}</span><span>draw ${pct(m.p_draw, 0)}</span><span>${esc(m.away)} ${pct(m.p_away, 0)}</span></div>${exp}`;
}
function predictionPanel(m) {
  const p = m.prediction;
  if (!p) return `<p class="quiet">No completed-match prediction check yet.</p>`;
  const predProb = outcomeProb(p, p.pred_outcome);
  return `
    ${statRow("pre-match call", `${esc(outcomeText(m, p.pred_outcome))}${typeof predProb === "number" ? ` (${pct(predProb, 0)})` : ""}`)}
    ${statRow("actual outcome", esc(outcomeText(m, p.actual_outcome)))}
    ${statRowHtml("outcome result", predictionMark(p.outcome_hit))}
    ${statRow("top score", `${esc(p.top_score)}${scoreProbText(p)}`)}
    ${statRow("actual score", esc(p.actual_score))}
    ${statRowHtml("score result", predictionMark(p.score_hit))}
    ${statRow("actual-outcome prob", typeof p.prob_actual === "number" ? pct(p.prob_actual, 1) : "")}
    ${statRow("log loss", typeof p.logloss === "number" ? p.logloss.toFixed(3) : "")}`;
}
function moments(m) {
  const events = [...(m.feed?.events ?? [])].sort((a, b) => minuteSort(a.minute) - minuteSort(b.minute));
  if (!events.length) return `<p class="quiet">${matchPhase(m) === "live" ? "No public moments posted yet." : "No goal moments in the public feed yet."}</p>`;
  return `<ol class="moment-list">${events.map((e) =>
    `<li><span class="minute">${esc(e.minute)}'</span><span class="event-team ${esc(e.side)}">${esc(e.team)}</span><strong>${esc(e.player)}</strong><em>${esc(e.detail || e.type)}</em></li>`).join("")}</ol>`;
}
function teamContext(m) {
  const rows = [m.home, m.away].map((name) => {
    const t = tmap[name];
    if (!t) return "";
    return `<tr><td>${esc(t.code)}</td><td>${esc(String(t.pts))}</td><td>${esc(`${t.gf}-${t.ga}`)}</td><td>${esc(String(t.elo))}</td><td>${pct(t.p_r32, 0)}</td><td>${pct(t.p_champion)}</td></tr>`;
  }).join("");
  return `<table class="context-table"><tr><th>team</th><th>pts</th><th>GF-GA</th><th>Elo</th><th>adv</th><th>title</th></tr>${rows}</table>`;
}
function renderMatchDetail(m) {
  const score = scoreFor(m);
  const phase = matchPhase(m);
  const phaseText = phaseLabel(m);
  const feedScore = score ? `${score.home}–${score.away}` : "vs";
  const ht = Number.isFinite(m.feed?.ht_home) && Number.isFinite(m.feed?.ht_away) ? `${m.feed.ht_home}–${m.feed.ht_away}` : "";
  const elapsed = phase === "live" && m.kickoff_utc ? `${Math.max(1, Math.min(120, Math.floor((Date.now() - Date.parse(m.kickoff_utc)) / 60000)))}'` : "";
  renderStrip(m.date);
  $("#match-list").innerHTML = `<div class="match-detail">
    <div class="detail-top"><a class="back-link" href="#${esc(m.date)}">‹ day matches</a><span class="match-status ${phase}">${esc(phaseText)}</span></div>
    <div class="detail-score"><span>${esc(m.home)}</span><strong>${esc(feedScore)}</strong><span>${esc(m.away)}</span></div>
    <div class="detail-meta"><span>${esc(m.group ?? "")}</span><span>${esc(m.ground ?? "")}</span><time>${esc(matchTime(m))}</time></div>
    <div class="stats-grid">
      <section class="stat-panel">
        <h3>Match Stats</h3>
        ${statRow("status", esc(phaseText))}
        ${statRow("minute", esc(elapsed))}
        ${statRow("half-time", esc(ht))}
        ${statRow("public feed", esc(m.feed?.source ?? "openfootball/worldcup.json"))}
        ${statRow("source pull", esc(formatDateTime(data.data_pulled_utc)))}
        ${statRow("model", esc(modelState(m)))}
      </section>
      <section class="stat-panel">
        <h3>Model Snapshot</h3>
        ${modelSnapshot(m)}
      </section>
      <section class="stat-panel">
        <h3>Prediction Check</h3>
        ${predictionPanel(m)}
      </section>
      <section class="stat-panel wide">
        <h3>Moments</h3>
        ${moments(m)}
      </section>
      <section class="stat-panel wide">
        <h3>Team Context</h3>
        ${teamContext(m)}
      </section>
    </div>
  </div>`;
  requestAnimationFrame(() => $("#matches").scrollIntoView({ block: "start" }));
}

// day-by-day matches: open on today, each day linkable via #YYYY-MM-DD
const matchDays = [...new Set(data.matches.map((m) => m.date))].sort();
const todayISO = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
const TODAY = todayISO();
const dayLabel = (iso, opts) => new Date(iso + "T00:00:00").toLocaleDateString("en-US", opts);
const defaultDay = () => matchDays.includes(TODAY) ? TODAY : (matchDays.find((d) => d > TODAY) ?? matchDays[matchDays.length - 1]);
const sectionIds = new Set(["odds", "prediction-results", "matches", "groups", "scorers", "about"]);
let activeDay = defaultDay();
const currentRoute = () => {
  const h = decodeURIComponent(location.hash.replace(/^#/, ""));
  if (h.startsWith("match/")) {
    const match = matchesById[h.slice(6)];
    if (match) return { type: "match", match };
  }
  if (matchDays.includes(h)) return { type: "day", day: h };
  if (sectionIds.has(h)) return { type: "section", id: h };
  return { type: "day", day: activeDay };
};
const currentDay = () => {
  const route = currentRoute();
  if (route.type === "match") return route.match.date;
  if (route.type === "day") return route.day;
  return activeDay;
};

function renderStrip(active) {
  $("#day-strip").innerHTML = matchDays.map((d) => {
    const cls = ["day-chip", d === active ? "active" : "", d === TODAY ? "is-today" : ""].filter(Boolean).join(" ");
    return `<button class="${cls}" data-day="${d}"><span class="wd">${dayLabel(d, { weekday: "short" })}</span><span class="dd">${dayLabel(d, { day: "numeric" })}</span></button>`;
  }).join("");
  const act = $("#day-strip .active"), strip = $("#day-strip"); // center the chip without scrolling the page
  if (act) strip.scrollLeft = act.offsetLeft - strip.clientWidth / 2 + act.clientWidth / 2;
}
function renderDayMatches(d) {
  const list = data.matches.filter((m) => m.date === d);
  const tag = d === TODAY ? ` <span class="today-tag">today</span>` : "";
  const head = `<div class="day-head">${dayLabel(d, { weekday: "long", month: "long", day: "numeric" })}${tag}</div>`;
  const body = list.length ? `<div class="match-grid">${list.map(matchCard).join("")}</div>` : `<p class="no-matches">No matches scheduled.</p>`;
  $("#match-list").innerHTML = head + body;
}
const selectDay = (d) => { activeDay = d; renderStrip(d); renderDayMatches(d); };
$("#day-strip").addEventListener("click", (e) => { const b = e.target.closest(".day-chip"); if (b) location.hash = b.dataset.day; });
const step = (dir) => { const i = matchDays.indexOf(currentDay()); location.hash = matchDays[Math.min(matchDays.length - 1, Math.max(0, i + dir))]; };
$("#day-prev").onclick = () => step(-1);
$("#day-next").onclick = () => step(1);
const scrollToSection = (id) => {
  const scroll = () => document.getElementById(id)?.scrollIntoView({ block: "start" });
  requestAnimationFrame(() => requestAnimationFrame(scroll));
  setTimeout(scroll, 600);
  setTimeout(scroll, 1400);
};
function renderRoute() {
  const route = currentRoute();
  if (route.type === "match") renderMatchDetail(route.match);
  else if (route.type === "section") { selectDay(activeDay); scrollToSection(route.id); }
  else selectDay(route.day);
}
window.addEventListener("hashchange", renderRoute);
renderRoute();

function renderPredictionResults() {
  const summary = data.prediction_summary;
  const rows = data.matches.filter((m) => m.prediction).sort((a, b) =>
    a.date === b.date ? a.id.localeCompare(b.id) : a.date.localeCompare(b.date));
  if (!summary || !summary.n) {
    $("#prediction-summary").innerHTML = `<p class="quiet">No completed matches to grade yet.</p>`;
    $("#prediction-list").innerHTML = "";
    return;
  }
  const metric = (label, value, sub = "") => `<div class="metric-card"><span>${esc(label)}</span><strong>${esc(value)}</strong>${sub ? `<em>${esc(sub)}</em>` : ""}</div>`;
  $("#prediction-summary").innerHTML = `<div class="prediction-scoreboard">
    ${metric("Outcome calls", `${summary.outcome_correct}/${summary.n}`, `${pct(summary.outcome_pct, 0)} correct`)}
    ${metric("Exact scores", `${summary.score_correct}/${summary.n}`, `${pct(summary.score_pct, 0)} correct`)}
    ${metric("Mean log loss", Number(summary.mean_logloss).toFixed(3), `uniform ${Number(summary.uniform_logloss).toFixed(3)}`)}
    ${metric("Avg actual prob", pct(summary.mean_prob_actual, 1), `through ${summary.results_through ?? "—"}`)}
  </div>`;
  $("#prediction-list").innerHTML = `<div class="prediction-table-wrap"><table class="prediction-table">
    <tr><th>match</th><th>actual</th><th>outcome call</th><th>top score</th></tr>
    ${rows.map((m) => {
      const p = m.prediction;
      const predProb = outcomeProb(p, p.pred_outcome);
      const date = dayLabel(m.date, { month: "short", day: "numeric" });
      return `<tr>
        <td><a href="#match/${encodeURIComponent(m.id)}">${esc(date)} · ${esc(m.home)} vs ${esc(m.away)}</a></td>
        <td>${esc(p.actual_score)}</td>
        <td>${esc(outcomeText(m, p.pred_outcome))}${typeof predProb === "number" ? ` ${pct(predProb, 0)}` : ""} ${predictionMark(p.outcome_hit)}</td>
        <td>${esc(p.top_score)}${scoreProbText(p)} ${predictionMark(p.score_hit)}</td>
      </tr>`;
    }).join("")}
  </table></div>`;
}
renderPredictionResults();

// knockout bracket
const ROUND_SHORT = { "Round of 32": "Round of 32", "Round of 16": "Round of 16", "Quarter-final": "Quarterfinals", "Semi-final": "Semifinals", "Final": "Final" };
const ROUND_ORDER = ["Round of 32", "Round of 16", "Quarter-final", "Semi-final", "Final"];
const bktFlag = (fifa, resolved) => {
  const f = resolved ? FLAG_CODE[fifa] : null;
  return f ? `<img class="bkt-flag" src="./flags/4x3/${f}.svg" alt="" loading="lazy">` : `<span class="bkt-flag ph"></span>`;
};
const bktTeamRow = (name, fifa, score, isWin, resolved) =>
  `<div class="bkt-team ${isWin ? "win" : ""} ${resolved ? "" : "tbd"}">${bktFlag(fifa, resolved)}<span class="bkt-name">${esc(name)}</span><span class="bkt-score">${Number.isFinite(score) ? score : ""}</span></div>`;
const bktMatch = (b) => `<div class="bkt-match">
    ${bktTeamRow(b.team1, b.code1, b.hs, !!b.winner && b.winner === b.team1, !!b.code1)}
    ${bktTeamRow(b.team2, b.code2, b.as_, !!b.winner && b.winner === b.team2, !!b.code2)}
  </div>`;
function renderBracket() {
  const bracket = data.bracket ?? [];
  const section = $("#bracket");
  if (!section || !bracket.length) return;
  const byRound = {};
  for (const b of bracket) (byRound[b.round] ??= []).push(b);
  $("#bracket-tree").innerHTML = ROUND_ORDER.map((round) => {
    const ms = (byRound[round] ?? []).slice().sort((a, b) => a.num - b.num);
    if (!ms.length) return "";
    return `<div class="bracket-round"><div class="bkt-round-label">${esc(ROUND_SHORT[round] ?? round)}</div><div class="bkt-col">${ms.map(bktMatch).join("")}</div></div>`;
  }).join("");
  const third = bracket.find((b) => b.round === "Match for third place");
  $("#bracket-third").innerHTML = third
    ? `<div class="bkt-third"><span class="bkt-third-label">Third place</span>${bktMatch(third)}</div>` : "";
  section.hidden = false;
}
renderBracket();

const groupMatches = (g) => data.matches
  .filter((m) => m.group === `Group ${g}`)
  .sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
const groupStandings = (g) => {
  const rows = data.groups[g].map((n) => {
    const t = tmap[n];
    return `<tr><td title="${esc(t.name)}">${esc(t.code)}</td><td>${t.played}</td><td>${t.pts}</td><td>${t.gf - t.ga}</td><td class="adv">${pct(t.p_r32, 0)}</td></tr>`;
  }).join("");
  return `<table class="group-standings"><tr><th>team</th><th>P</th><th>pts</th><th>GD</th><th>adv</th></tr>${rows}</table>`;
};
function renderGroupGrid() {
  $("#group-grid").innerHTML = letters.map((g) =>
    `<div class="group-card" role="button" tabindex="0" data-group="${esc(g)}"><h3>GROUP ${esc(g)}</h3>${groupStandings(g)}</div>`
  ).join("");
}
function showGroupGrid() {
  $("#group-grid").style.display = "";
  $("#group-detail").style.display = "none";
  $("#group-detail").innerHTML = "";
}
function openGroup(g) {
  const list = groupMatches(g);
  const body = list.length ? `<div class="match-grid">${list.map(matchCard).join("")}</div>` : `<p class="no-matches">No fixtures.</p>`;
  $("#group-detail").innerHTML = `
    <div class="detail-top"><button class="back-link" id="group-back">‹ all groups</button></div>
    <div class="group-detail-head">Group ${esc(g)} <span class="h2-note">standings &amp; fixtures</span></div>
    ${groupStandings(g)}
    <div class="group-fixtures-head">Fixtures <span class="h2-note">past &amp; upcoming</span></div>
    ${body}`;
  $("#group-grid").style.display = "none";
  $("#group-detail").style.display = "";
  requestAnimationFrame(() => $("#groups").scrollIntoView({ block: "start" }));
}
$("#group-grid").addEventListener("click", (e) => {
  const card = e.target.closest(".group-card");
  if (card) openGroup(card.dataset.group);
});
$("#group-grid").addEventListener("keydown", (e) => {
  if (e.key !== "Enter" && e.key !== " ") return;
  const card = e.target.closest(".group-card");
  if (card) { e.preventDefault(); openGroup(card.dataset.group); }
});
$("#group-detail").addEventListener("click", (e) => { if (e.target.closest("#group-back")) showGroupGrid(); });
renderGroupGrid();
showGroupGrid();

$("#scorer-list").innerHTML = data.scorers.map((s) =>
  `<li>${s.name} <span class="s-goals">${s.goals}</span> <span class="s-team">${s.team}</span></li>`).join("");
