// Reads data/latest.json (the current run) and data/history.jsonl (one run per line).
// The format of a run is described in data/contract.json.

const REFRESH_SECONDS = 60;
// The monitor runs every 12 hours. After 20 hours without a run the page says "not running".
const STOPPED_AFTER_SECONDS = 20 * 60 * 60;
const SEVERITY = ["ok", "no_verdict", "alert"];
const RESULT_WORDS = { ok: "OK", no_verdict: "No verdict", alert: "Alert" };
const ETHERSCAN = "https://etherscan.io/address/";
const SPOKE = "0xEC3582fcDc34078a4B7a8c75a5a3AE46f48525aB";
const CHRONICLE = "0x9a3bF392f86acd1b1EC07d026B326302eAED7488";

const CHECKS = [
  { id: "spoke_price_age", element: "check-age", title: "Time since the last price update",
    value: "age_hours", limit: "limit_hours", unit: "h", explain: explainAge },
  { id: "spoke_chronicle_divergence", element: "check-divergence", title: "Difference between Spoke and Chronicle price",
    value: "divergence_pct", limit: "limit_pct", unit: "%", explain: explainDivergence },
];

// The day (unix time divided by 86400) whose scans are listed under the strip; null = none
let selectedDay = null;
// The timestamp of the scan that the readings table shows; null = the last scan of the day
let selectedScan = null;

const byId = (id) => document.getElementById(id);
const escapeHtml = (text) => String(text).replace(/[&<>"]/g, (c) => `&#${c.charCodeAt(0)};`);
const link = (address, text) => `<a href="${ETHERSCAN}${address}#readContract" target="_blank" rel="noopener">${text}</a>`;

function formatTime(seconds) {
  const text = new Date(seconds * 1000).toLocaleString("en-GB", {
    timeZone: "UTC", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
  });
  return `${text} UTC`;
}

function formatDay(seconds) {
  return new Date(seconds * 1000).toLocaleString("en-GB", { timeZone: "UTC", day: "numeric", month: "short" });
}

function formatAgo(seconds) {
  if (seconds < 90) return "1 minute ago";
  if (seconds < 5400) return `${Math.round(seconds / 60)} minutes ago`;
  if (seconds < 172800) return `${Math.round(seconds / 3600)} hours ago`;
  return `${Math.round(seconds / 86400)} days ago`;
}

// Prices are integer strings with 18 decimals. BigInt keeps them exact.
function formatPrice(price) {
  if (!price) return "—";
  const digits = BigInt(price).toString().padStart(19, "0");
  return `${digits.slice(0, -18)}.${digits.slice(-18, -12)}<small>${digits.slice(-12, -8)}</small>`;
}

// The verdict of a check. With more than one chain: the worst one (the first chain on a tie).
function findVerdict(run, checkId) {
  return run.verdicts.filter((verdict) => verdict.check === checkId)
    .sort((a, b) => SEVERITY.indexOf(b.result) - SEVERITY.indexOf(a.result))[0];
}

function explainAge(verdict) {
  const since = `<strong>${formatTime(verdict.computed_at)}</strong>`;
  if (verdict.result === "alert") {
    const over = (verdict.age_hours - verdict.limit_hours).toFixed(1);
    return `No new price since ${since}. That is ${over} h over the limit. Look at the ${link(SPOKE, "Spoke")}.`;
  }
  return `Last price update: ${since}. Weekend hours do not count.`;
}

function explainDivergence(verdict) {
  const sources = `the ${link(SPOKE, "Spoke")} and the ${link(CHRONICLE, "Chronicle oracle")}`;
  if (verdict.result === "alert") {
    return `The two prices differ by more than ${verdict.limit_pct} %. Look at ${sources}.`;
  }
  return `Compares ${sources} at the same block.`;
}

// The result of the shown scan. "Monitor not running" is about the latest run and wins over all.
function renderStatus(shown, latest) {
  const silence = Date.now() / 1000 - latest.run_at;
  let state = shown.overall;
  let detail = `Checked ${formatAgo(silence)}, at ${formatTime(latest.timestamp)}.`;
  if (selectedDay !== null) {
    detail = `Scan of ${formatTime(shown.timestamp)}. The latest scan, ${formatAgo(silence)}: ${RESULT_WORDS[latest.overall]}.`;
  }
  if (state === "alert") {
    const failed = CHECKS.filter((check) => findVerdict(shown, check.id)?.result === "alert");
    detail = `Over the limit: ${failed.map((check) => check.title).join("; ")}. ${detail}`;
  }
  if (state === "no_verdict") {
    detail = `The monitor could not read the chain. This is not an all-clear. ${detail}`;
  }
  if (silence > STOPPED_AFTER_SECONDS) {
    state = "stopped";
    detail = `The last scan was ${formatAgo(silence)}. The values below are the last known ones `
      + `(${RESULT_WORDS[latest.overall]}) and can be wrong now.`;
  }
  byId("status").dataset.state = state;
  byId("status-word").textContent = state === "stopped" ? "Monitor not running" : RESULT_WORDS[state];
  byId("status-detail").textContent = detail;
  document.body.classList.toggle("stale", state === "stopped");
}

function renderLoadError(error) {
  byId("status").dataset.state = "no_verdict";
  byId("status-word").textContent = "No data";
  byId("status-detail").textContent = `The page could not load the monitor's files (${error.message}).`;
}

// The run that the status, the scan list, the check cards and the tables show:
// the selected scan, or the last scan of the selected day, or the latest run if no day is selected.
function findShownRun(history, latest) {
  if (selectedDay === null) return latest;
  const runs = history.filter((run) => Math.floor(run.timestamp / 86400) === selectedDay);
  return runs.find((run) => run.timestamp === selectedScan) ?? runs[runs.length - 1];
}

function renderSelection(history, latest) {
  const shown = findShownRun(history, latest);
  const when = selectedDay === null ? "latest scan" : formatTime(shown.timestamp);
  renderStatus(shown, latest);
  renderDays(history, latest);
  renderDayScans(history, latest, shown);
  CHECKS.forEach((check) => renderCheck(check, shown, history, when));
  renderReadings(shown, when);
}

function renderDays(history, latest) {
  const worstByDay = new Map();
  for (const run of history) {
    const day = Math.floor(run.timestamp / 86400);
    const known = worstByDay.get(day) || { result: "ok", scans: 0 };
    const worse = SEVERITY.indexOf(run.overall) > SEVERITY.indexOf(known.result);
    worstByDay.set(day, { result: worse ? run.overall : known.result, scans: known.scans + 1 });
  }
  const days = [...worstByDay.keys()];
  const first = Math.min(...days);
  const last = Math.max(...days);
  let cells = "";
  for (let day = first; day <= last; day++) {
    const known = worstByDay.get(day);
    const title = known ? `${RESULT_WORDS[known.result]}, ${known.scans} scans` : "no scan";
    cells += `<button type="button" data-day="${day}" data-result="${known ? known.result : ""}" `
      + `aria-pressed="${day === selectedDay}" ${known ? "" : "disabled"} title="${formatDay(day * 86400)}: ${title}"></button>`;
  }
  byId("days-strip").innerHTML = cells;
  byId("days-strip").onclick = (event) => {
    const day = Number(event.target.dataset.day);
    if (!day) return;
    selectedDay = day === selectedDay ? null : day;
    selectedScan = null;
    renderSelection(history, latest);
  };
  byId("days-first").textContent = formatDay(first * 86400);
  byId("days-last").textContent = formatDay(last * 86400);
}

// The scans of the selected day, one row per scan. A check with no verdict shows "Could not read".
function renderDayScans(history, latest, shown) {
  byId("day-scans").hidden = selectedDay === null;
  if (selectedDay === null) return;
  const runs = history.filter((run) => Math.floor(run.timestamp / 86400) === selectedDay);
  byId("day-scans-body").onclick = (event) => {
    selectedScan = Number(event.target.closest("tr").dataset.scan);
    renderSelection(history, latest);
  };
  byId("day-scans-title").textContent = `${formatDay(selectedDay * 86400)}: ${runs.length} scans`;
  byId("day-scans-body").innerHTML = runs.map((run) => `<tr data-scan="${run.timestamp}" aria-selected="${run === shown}">
    <td>${formatTime(run.timestamp)}</td>
    <td class="result-${run.overall}">${RESULT_WORDS[run.overall]}</td>
    ${CHECKS.map((check) => {
      const verdict = findVerdict(run, check.id);
      const text = verdict[check.value] === undefined ? "Could not read" : `${verdict[check.value]} ${check.unit}`;
      return `<td class="result-${verdict.result}">${text}</td>`;
    }).join("")}
    <td>${run.readings.chains[0].block ?? "—"}</td>
  </tr>`).join("");
}

function renderCheck(check, shown, history, when) {
  const verdict = findVerdict(shown, check.id);
  const card = byId(check.element);
  card.dataset.result = verdict.result;
  let body = `<p class="value">—</p><div class="meter"></div><p class="explain">${escapeHtml(verdict.reason)}</p>`;
  if (verdict.result !== "no_verdict") {
    const share = Math.min(100, verdict[check.value] / verdict[check.limit] * 100);
    body = `<p class="value">${verdict[check.value]}${check.unit} <small>limit ${verdict[check.limit]}${check.unit}</small></p>`
      + `<div class="meter"><i style="width:${share}%"></i></div>`
      + `<p class="explain">${check.explain(verdict)}</p>`;
  }
  card.innerHTML = `<div class="check-head"><h2>${check.title}</h2>`
    + `<span class="result">${RESULT_WORDS[verdict.result]}</span></div>`
    + `<p class="label">${when[0].toUpperCase()}${when.slice(1)}</p>${body}`
    + `<svg class="chart" viewBox="0 0 600 170" role="img" aria-label="${check.title}, history"></svg>`
    + `<p class="hover"></p>`;
  renderChart(card, check, history, verdict[check.limit], shown.timestamp);
}

// Line of the value over time. A scan with no verdict breaks the line and gets a mark on the
// bottom axis: "could not check" is never drawn as a value.
function renderChart(card, check, history, latestLimit, shownTime) {
  const points = history.map((run) => ({ time: run.timestamp, verdict: findVerdict(run, check.id) }))
    .filter((point) => point.verdict);
  const limit = latestLimit ?? points.find((point) => point.verdict[check.limit])?.verdict[check.limit] ?? 0;
  const left = 36, right = 596, top = 8, bottom = 148;
  const firstTime = points[0].time;
  const timeSpan = Math.max(1, points[points.length - 1].time - firstTime);
  const highest = Math.max(limit, ...points.map((point) => point.verdict[check.value] ?? 0)) * 1.15;
  const x = (time) => left + (time - firstTime) / timeSpan * (right - left);
  const y = (value) => bottom - value / highest * (bottom - top);

  let line = "", over = "", failed = "", previous = null;
  for (const point of points) {
    const value = point.verdict[check.value];
    if (value === undefined) {
      failed += `M${x(point.time)},${bottom - 5}V${bottom + 5}`;
      previous = null;
      continue;
    }
    const step = `${previous ? "L" : "M"}${x(point.time).toFixed(1)},${y(value).toFixed(1)}`;
    line += step;
    if (previous && point.verdict.result === "alert") {
      over += `M${x(previous.time).toFixed(1)},${y(previous.verdict[check.value]).toFixed(1)}${step.replace("M", "L")}`;
    }
    previous = point;
  }

  const svg = card.querySelector("svg");
  svg.innerHTML = `<line class="limit" x1="${left}" x2="${right}" y1="${y(limit)}" y2="${y(limit)}"/>`
    + `<text x="${left - 6}" y="${y(limit) + 4}" text-anchor="end">${limit}</text>`
    + `<text x="${left - 6}" y="${bottom + 4}" text-anchor="end">0</text>`
    + `<text x="${left}" y="166">${formatDay(firstTime)}</text>`
    + `<text x="${right}" y="166" text-anchor="end">${formatDay(firstTime + timeSpan)}</text>`
    + `<path class="line" d="${line}"/><path class="line over" d="${over}"/><path class="failed" d="${failed}"/>`
    + `<line class="cursor" y1="${top}" y2="${bottom}" visibility="hidden"/>`;

  const cursor = svg.querySelector(".cursor");
  const hover = card.querySelector(".hover");
  // The cursor rests on the shown scan. It follows the mouse over the chart and then goes back.
  const moveCursor = (time) => {
    const nearest = points.reduce((a, b) => (Math.abs(b.time - time) < Math.abs(a.time - time) ? b : a));
    const value = nearest.verdict[check.value];
    cursor.setAttribute("x1", x(nearest.time));
    cursor.setAttribute("x2", x(nearest.time));
    cursor.setAttribute("visibility", "visible");
    hover.textContent = `${formatTime(nearest.time)}: `
      + `${value === undefined ? nearest.verdict.reason : `${value} ${check.unit}`}, ${RESULT_WORDS[nearest.verdict.result]}`;
  };
  svg.onmousemove = (event) => {
    const box = svg.getBoundingClientRect();
    moveCursor(firstTime + ((event.clientX - box.left) / box.width * 600 - left) / (right - left) * timeSpan);
  };
  svg.onmouseleave = () => moveCursor(shownTime);
  moveCursor(shownTime);
}

// The Spoke price of a chain next to Ethereum's. A metric, not a check: it gives no alert.
function compareWithEthereum(reading, ethereum) {
  if (reading === ethereum || !reading.price || !ethereum.price) return "—";
  const difference = BigInt(reading.price) - BigInt(ethereum.price);
  if (difference === 0n) return "same price";
  return `differs by ${Number((difference < 0n ? -difference : difference) * 1000000n / BigInt(ethereum.price)) / 10000}%`;
}

function renderReadings(latest, when) {
  byId("readings-title").textContent = `What the monitor read, ${when}`;
  const chronicle = { ...latest.readings.chronicle, name: "Chronicle oracle, ethereum", address: CHRONICLE };
  const spokes = latest.readings.chains.map((reading) => ({ ...reading, name: `Spoke, ${reading.name}`, address: SPOKE }));
  byId("readings-body").innerHTML = [...spokes, chronicle].map((reading) => `<tr>
    <td>${reading.chain_id && reading.chain_id !== 1 ? escapeHtml(reading.name) : link(reading.address, escapeHtml(reading.name))}</td>
    <td>${reading.block ?? "—"}</td>
    <td>${formatPrice(reading.price)}</td>
    <td>${reading.computed_at ? formatTime(reading.computed_at) : "—"}</td>
    <td>${reading.chain_id ? compareWithEthereum(reading, spokes[0]) : "—"}</td>
    <td class="read-${reading.status}">${reading.status === "ok" ? "ok" : `failed: ${escapeHtml(reading.error)}`}</td>
  </tr>`).join("");
}

async function load() {
  try {
    const [latestResponse, historyResponse] = await Promise.all([
      fetch("data/latest.json", { cache: "no-store" }),
      fetch("data/history.jsonl", { cache: "no-store" }),
    ]);
    if (!latestResponse.ok || !historyResponse.ok) throw new Error("file not found");
    const latest = await latestResponse.json();
    const history = (await historyResponse.text()).split("\n").filter(Boolean).map(JSON.parse)
      .sort((a, b) => a.timestamp - b.timestamp);
    renderSelection(history, latest);
  } catch (error) {
    renderLoadError(error);
  }
}

load();
setInterval(load, REFRESH_SECONDS * 1000);
