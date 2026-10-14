(() => {
"use strict";
const $ = (selector) => document.querySelector(selector);
const SVG_NS = "http://www.w3.org/2000/svg";
const EMOTION_NAMES = {joy: "Joy", trust: "Trust", anger: "Anger", fear: "Fear", sadness: "Sadness"};
const MAX_FILE_BYTES = 15 * 1024 * 1024;
let result = null;
let length = "medium";

const fmt = (x, digits = 2) => (x < 0 ? "−" : "+") + Math.abs(x).toFixed(digits);
const pct = (x) => Math.round(x * 100) + "%";

function make(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function setStatus(message, isError) {
  const status = $("#status");
  status.textContent = message;
  status.className = "status" + (isError ? " err" : "");
}
async function api(path, options) {
  const response = await fetch(path, options);
  let data = {};
  try { data = await response.json(); } catch (e) { /* non-JSON error body */ }
  if (!response.ok) throw new Error(data.error || "Request failed (" + response.status + ").");
  return data;
}

/* ---------- Talking to the Python server ---------- */
async function analyzeText(text, source) {
  setStatus("Analyzing…");
  try {
    result = await api("/api/analyze", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({text}),
    });
    finish(source);
  } catch (error) { setStatus(error.message, true); }
}
async function analyzeFile(file) {
  if (!file) return;
  if (file.size > MAX_FILE_BYTES) { setStatus("That file is over 15 MB. Try a smaller one or paste the text.", true); return; }
  setStatus("Reading " + file.name + "…");
  try {
    result = await api("/api/analyze-file", {
      method: "POST",
      headers: {"X-Filename": encodeURIComponent(file.name), "Content-Type": "application/octet-stream"},
      body: file,
    });
    $("#txt").value = result.text;
    finish(file.name);
  } catch (error) { setStatus(error.message, true); }
}
function finish(source) {
  setStatus((source ? "Analyzed " + source + ". " : "Analyzed. ") + result.words.toLocaleString() + " words." +
    (result.truncated ? " Only the first 300,000 characters were analyzed." : ""));
  render();
}

/* ---------- Rendering ---------- */
function render() {
  $("#results").hidden = false;
  $("#vTitle").textContent = result.verdict;
  $("#vTitle").className = "verdict " + (result.verdict_tone === "neu" ? "" : result.verdict_tone);
  $("#vSub").textContent = "Average sentence score " + fmt(result.avg_score) + ". " + pct(result.shares.pos) +
    " of sentences are positive, " + pct(result.shares.neu) + " neutral and " + pct(result.shares.neg) + " negative.";
  $("#vMark").style.left = ((Math.max(-1, Math.min(1, result.avg_score / 0.5)) + 1) / 2 * 100) + "%";

  const kpis = $("#kpis");
  kpis.replaceChildren();
  [[result.words.toLocaleString(), "words"], [result.reading_time, "to read"],
   [result.sentences.length.toLocaleString(), "sentences"], [String(result.avg_sentence_length), "words per sentence"]]
    .forEach(([value, label]) => {
      const box = make("div", "kpi");
      box.append(make("b", "", value), make("span", "", label));
      kpis.append(box);
    });

  renderSummary();
  renderTopics();
  renderArc(result.arc);
  renderEmotions();
  renderStandouts();
  renderInsights();
  renderAnnotated();
}
function renderSummary() {
  const indexes = result.summaries[length];
  const total = result.sentences.length;
  $("#sumSub").textContent = total <= 3
    ? "The text is already very short, so the summary repeats most of it."
    : indexes.length + " of " + total + " sentences, kept in their original order. The dot shows each sentence's tone.";
  const list = $("#sumList");
  list.replaceChildren();
  if (!indexes.length) { list.append(make("li", "muted", "No sentences were long enough to summarise. Try a longer text.")); return; }
  indexes.forEach((i) => {
    const sentence = result.sentences[i];
    const item = make("li");
    item.append(make("i", "dot " + sentence.label), document.createTextNode(sentence.text));
    list.append(item);
  });
}
function renderTopics() {
  const box = $("#topics");
  box.replaceChildren();
  if (!result.keywords.length) { box.append(make("span", "muted", "No repeated topics found.")); return; }
  result.keywords.forEach((k) => {
    const chip = make("span", "word", k.word);
    if (k.count > 1) chip.append(make("small", "", String(k.count)));
    box.append(chip);
  });
}
function svg(tag, attrs) {
  const node = document.createElementNS(SVG_NS, tag);
  Object.entries(attrs || {}).forEach(([k, v]) => node.setAttribute(k, v));
  return node;
}
function renderArc(values) {
  const box = $("#arc");
  box.replaceChildren();
  box.hidden = values.length < 3;
  $("#arcNo").hidden = values.length >= 3;
  if (values.length < 3) return;
  const W = 640, H = 280, left = 44, right = 8, top = 12, bottom = 26;
  const plotW = W - left - right, plotH = H - top - bottom;
  const limit = Math.max(0.5, Math.ceil(Math.max(...values.map(Math.abs)) * 10) / 10);
  const y = (v) => top + (1 - (v + limit) / (2 * limit)) * plotH;
  const root = svg("svg", {viewBox: "0 0 " + W + " " + H, role: "img",
    "aria-label": "Bar chart of average sentiment from the start to the end of the text"});
  [[limit, "gridline"], [0, "zero"], [-limit, "gridline"]].forEach(([v, cls]) => {
    root.append(svg("line", {x1: left, x2: W - right, y1: y(v), y2: y(v), class: cls}));
    const label = svg("text", {x: left - 6, y: y(v) + 4, "text-anchor": "end"});
    label.textContent = (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(1);
    root.append(label);
  });
  const slot = plotW / values.length;
  values.forEach((v, i) => {
    const barTop = Math.min(y(v), y(0));
    const bar = svg("rect", {
      x: left + i * slot + slot * 0.1, width: slot * 0.8, y: barTop,
      height: Math.max(1, Math.abs(y(v) - y(0))),
      class: v > 0.05 ? "bar-pos" : v < -0.05 ? "bar-neg" : "bar-neu",
    });
    const tip = svg("title");
    tip.textContent = "Stretch " + (i + 1) + " of " + values.length + ": average " + fmt(v);
    bar.append(tip);
    root.append(bar);
  });
  [["Start", left, "start"], ["End", W - right, "end"]].forEach(([text, x, anchor]) => {
    const label = svg("text", {x, y: H - 8, "text-anchor": anchor});
    label.textContent = text;
    root.append(label);
  });
  box.append(root);
}
function renderEmotions() {
  const counts = result.emotions;
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const top = Math.max(1, ...Object.values(counts));
  $("#emoSub").textContent = total < 3
    ? "Very few emotion words were found, so this text is mostly neutral in wording."
    : total + " emotion words found. Bars compare the five emotions.";
  const box = $("#emo");
  box.replaceChildren();
  Object.keys(EMOTION_NAMES).forEach((name) => {
    const row = make("div", "row");
    const bar = make("div", "bar");
    const fill = make("i");
    fill.style.width = (counts[name] / top * 100) + "%";
    bar.append(fill);
    row.append(make("span", "", EMOTION_NAMES[name]), bar, make("b", "", String(counts[name])));
    box.append(row);
  });
}
function renderStandouts() {
  const fill = (selector, items, cls, none) => {
    const box = $(selector);
    box.replaceChildren();
    if (!items.length) { box.append(make("p", "nodata", none)); return; }
    items.forEach((s) => {
      const quote = make("div", "quote");
      const paragraph = make("p");
      paragraph.append(make("span", "badge " + cls, fmt(s.score)), document.createTextNode(s.text.length > 300 ? s.text.slice(0, 299).trim() + "…" : s.text));
      quote.append(paragraph);
      box.append(quote);
    });
  };
  fill("#topPos", result.standouts.positive, "pos", "No clearly positive sentences found.");
  fill("#topNeg", result.standouts.negative, "neg", "No clearly negative sentences found.");
}
function renderInsights() {
  const list = $("#insights");
  list.replaceChildren();
  result.insights.forEach((text) => list.append(make("li", "", text)));
}
function renderAnnotated() {
  const box = $("#annot");
  box.replaceChildren();
  result.annotated.forEach((segment) => {
    if (!segment.kind) { box.append(document.createTextNode(segment.text)); return; }
    const mark = make("mark", segment.kind, segment.text);
    mark.title = segment.tip || "";
    box.append(mark);
  });
}

/* ---------- Events ---------- */
document.querySelectorAll(".seg button").forEach((button) => button.addEventListener("click", () => {
  length = button.dataset.length;
  document.querySelectorAll(".seg button").forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
  if (result) renderSummary();
}));
$("#go").addEventListener("click", () => analyzeText($("#txt").value, ""));
$("#file").addEventListener("change", (event) => { analyzeFile(event.target.files[0]); event.target.value = ""; });
$("#copy").addEventListener("click", async () => {
  if (!result) return;
  const summary = result.summaries[length].map((i) => "- " + result.sentences[i].text).join("\n");
  const text = "Summary\n" + summary + "\n\nInsights\n" + result.insights.map((t) => "- " + t).join("\n");
  const button = $("#copy");
  let ok = false;
  try { await navigator.clipboard.writeText(text); ok = true; } catch (e) { /* clipboard blocked */ }
  button.textContent = ok ? "Copied" : "Copy failed. Select the text instead.";
  setTimeout(() => { button.textContent = "Copy summary and insights"; }, 2200);
});
const drop = $("#drop");
["dragenter", "dragover"].forEach((name) => drop.addEventListener(name, (e) => { e.preventDefault(); drop.classList.add("drag"); }));
["dragleave", "drop"].forEach((name) => drop.addEventListener(name, (e) => { e.preventDefault(); drop.classList.remove("drag"); }));
drop.addEventListener("drop", (e) => { const file = e.dataTransfer && e.dataTransfer.files[0]; if (file) analyzeFile(file); });

/* ---------- Start ---------- */
(async () => {
  try {
    const samples = await api("/api/samples");
    const box = $("#samples");
    Object.values(samples).forEach((sample) => {
      const chip = make("button", "chip", sample.title);
      chip.type = "button";
      chip.addEventListener("click", () => { $("#txt").value = sample.text; analyzeText(sample.text, "the sample"); });
      box.append(chip);
    });
    const first = Object.values(samples)[0];
    if (first) { $("#txt").value = first.text; analyzeText(first.text, "the sample"); }
  } catch (error) { setStatus(error.message, true); }
})();
})();
