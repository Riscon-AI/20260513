from __future__ import annotations

import json
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from fusion_material_ai import element_catalog, screen_candidates


DEFAULT_PROMPT = (
    "W-rich low activation ductile BCC alloy for plasma-facing fusion reactor components; "
    "prefer W Ti V Zr Ta Nb; density < 15"
)


INDEX_HTML = r"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Fusion Alloy AI Screener</title>
  <style>
    :root {
      --bg: #f6f7f2;
      --panel: #ffffff;
      --ink: #1d2424;
      --muted: #5c6765;
      --line: #d7ddd6;
      --teal: #0f766e;
      --blue: #1d4ed8;
      --amber: #b45309;
      --red: #b91c1c;
      --green: #15803d;
      --chip: #eef5f1;
      --shadow: 0 8px 24px rgba(24, 31, 30, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--bg);
      letter-spacing: 0;
    }
    header {
      border-bottom: 1px solid var(--line);
      background: #fcfdf9;
      position: sticky;
      top: 0;
      z-index: 5;
    }
    .topbar {
      max-width: 1280px;
      margin: 0 auto;
      padding: 14px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 260px;
    }
    .mark {
      width: 38px;
      height: 38px;
      display: grid;
      place-items: center;
      border: 1px solid #aab6b1;
      background: linear-gradient(135deg, #e8f2ed, #fff8e6);
      color: #16312f;
      font-weight: 800;
      border-radius: 8px;
    }
    h1 {
      margin: 0;
      font-size: 17px;
      line-height: 1.15;
    }
    .subtitle {
      margin-top: 2px;
      font-size: 12px;
      color: var(--muted);
    }
    .status {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 13px;
      color: var(--muted);
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--green);
    }
    main {
      max-width: 1280px;
      margin: 0 auto;
      padding: 18px 20px 36px;
    }
    .layout {
      display: grid;
      grid-template-columns: 390px minmax(0, 1fr);
      gap: 18px;
      align-items: start;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }
    .panel h2 {
      font-size: 15px;
      margin: 0;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
    }
    .body { padding: 16px; }
    label {
      display: block;
      font-size: 12px;
      font-weight: 700;
      margin-bottom: 7px;
      color: #303a39;
    }
    textarea, input {
      width: 100%;
      border: 1px solid #bdc8c3;
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      font: inherit;
      font-size: 14px;
      padding: 10px 11px;
      outline: none;
    }
    textarea:focus, input:focus {
      border-color: var(--teal);
      box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.14);
    }
    textarea {
      resize: vertical;
      min-height: 126px;
      line-height: 1.45;
    }
    .grid2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-top: 14px;
    }
    .button-row {
      display: flex;
      gap: 10px;
      margin-top: 16px;
    }
    button {
      border: 1px solid transparent;
      border-radius: 6px;
      padding: 10px 12px;
      font-weight: 750;
      font-size: 14px;
      cursor: pointer;
      background: var(--teal);
      color: #fff;
      min-height: 40px;
    }
    button.secondary {
      background: #fff;
      color: var(--ink);
      border-color: #b7c2bc;
    }
    button:disabled {
      opacity: 0.55;
      cursor: wait;
    }
    .pipeline {
      display: grid;
      gap: 8px;
      margin-top: 16px;
    }
    .step {
      display: grid;
      grid-template-columns: 30px 1fr;
      gap: 10px;
      align-items: start;
      padding: 10px;
      border: 1px solid #dce3df;
      border-radius: 8px;
      background: #fbfcf8;
    }
    .step-index {
      width: 26px;
      height: 26px;
      border-radius: 6px;
      display: grid;
      place-items: center;
      background: #e1efea;
      color: #0a5d56;
      font-size: 12px;
      font-weight: 800;
    }
    .step-title {
      font-size: 13px;
      font-weight: 800;
    }
    .step-text {
      margin-top: 2px;
      font-size: 12px;
      color: var(--muted);
      line-height: 1.35;
    }
    .summary {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 14px;
    }
    .metric {
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 11px 12px;
    }
    .metric-value {
      font-size: 22px;
      font-weight: 850;
    }
    .metric-label {
      margin-top: 2px;
      font-size: 12px;
      color: var(--muted);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th, td {
      border-bottom: 1px solid #e3e8e4;
      text-align: left;
      vertical-align: top;
      padding: 10px 8px;
    }
    th {
      font-size: 12px;
      color: #44504e;
      background: #f8faf5;
      position: sticky;
      top: 67px;
      z-index: 2;
    }
    .formula {
      font-weight: 850;
      white-space: nowrap;
    }
    .score {
      font-variant-numeric: tabular-nums;
      font-weight: 800;
    }
    .tag {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 3px 7px;
      background: var(--chip);
      color: #27413d;
      font-size: 12px;
      margin: 2px 3px 2px 0;
      border: 1px solid #d7e5df;
    }
    .risk {
      color: var(--amber);
    }
    .risk.high {
      color: var(--red);
      font-weight: 700;
    }
    .bars {
      min-width: 180px;
      display: grid;
      gap: 5px;
    }
    .bar {
      display: grid;
      grid-template-columns: 68px 1fr 34px;
      gap: 6px;
      align-items: center;
      font-size: 11px;
      color: var(--muted);
    }
    .track {
      height: 7px;
      background: #e7ece7;
      border-radius: 999px;
      overflow: hidden;
    }
    .fill {
      height: 100%;
      background: var(--blue);
      border-radius: inherit;
    }
    .fill.ductility { background: var(--teal); }
    .fill.activation { background: var(--green); }
    .fill.temp { background: var(--amber); }
    .empty {
      padding: 40px 16px;
      text-align: center;
      color: var(--muted);
      border: 1px dashed #cbd5cf;
      border-radius: 8px;
      background: #fbfcf8;
    }
    .disclaimer {
      margin-top: 12px;
      font-size: 12px;
      color: #6b5240;
      line-height: 1.45;
      background: #fff8eb;
      border: 1px solid #f1d9b7;
      border-radius: 8px;
      padding: 10px 11px;
    }
    @media (max-width: 980px) {
      .layout { grid-template-columns: 1fr; }
      .summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      th { position: static; }
    }
    @media (max-width: 640px) {
      .topbar { align-items: flex-start; flex-direction: column; }
      .grid2, .summary { grid-template-columns: 1fr; }
      table { display: block; overflow-x: auto; }
    }
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <div class="brand">
        <div class="mark">FA</div>
        <div>
          <h1>Fusion Alloy AI Screener</h1>
          <div class="subtitle">DuctGPT형 후보 생성, physics-informed screening, 실험 우선순위화</div>
        </div>
      </div>
      <div class="status"><span class="dot"></span><span id="statusText">로컬 모델 준비됨</span></div>
    </div>
  </header>
  <main>
    <div class="layout">
      <section class="panel">
        <h2>탐색 요청</h2>
        <div class="body">
          <label for="prompt">자연어 소재 목표</label>
          <textarea id="prompt"></textarea>
          <div class="grid2">
            <div>
              <label for="samples">후보 수</label>
              <input id="samples" type="number" min="100" max="10000" step="100" value="2500" />
            </div>
            <div>
              <label for="top">표시 수</label>
              <input id="top" type="number" min="5" max="100" step="5" value="25" />
            </div>
          </div>
          <div class="button-row">
            <button id="run">후보 탐색</button>
            <button id="reset" class="secondary">기본값</button>
          </div>
          <div class="disclaimer">
            이 도구는 합금 후보를 줄이는 스크리닝 보조 시스템입니다. 실제 핵융합로 소재로 판단하려면 DFT, CALPHAD, 조사 손상, 합성, 인장시험 검증이 필요합니다.
          </div>
          <div class="pipeline" aria-label="workflow">
            <div class="step"><div class="step-index">1</div><div><div class="step-title">Prompt</div><div class="step-text">원소군, W-rich, 저방사화, 연성, 밀도 제한 등 목표를 해석</div></div></div>
            <div class="step"><div class="step-index">2</div><div><div class="step-title">Generate</div><div class="step-text">내화 다원계 합금 조성을 무작위/시드 조합으로 생성</div></div></div>
            <div class="step"><div class="step-index">3</div><div><div class="step-title">Predict</div><div class="step-text">VEC, 원자 크기 불일치, 혼합 엔트로피, 융점, 밀도 기반 점수화</div></div></div>
            <div class="step"><div class="step-index">4</div><div><div class="step-title">Prioritize</div><div class="step-text">DFT와 소량 합성으로 넘길 상위 후보와 위험 플래그 산출</div></div></div>
          </div>
        </div>
      </section>
      <section>
        <div class="summary" id="summary">
          <div class="metric"><div class="metric-value">-</div><div class="metric-label">생성 후보</div></div>
          <div class="metric"><div class="metric-value">-</div><div class="metric-label">최고 점수</div></div>
          <div class="metric"><div class="metric-value">-</div><div class="metric-label">우선 검증 후보</div></div>
          <div class="metric"><div class="metric-value">-</div><div class="metric-label">평균 불확실성</div></div>
        </div>
        <section class="panel">
          <h2>후보 합금 랭킹</h2>
          <div class="body" id="results">
            <div class="empty">탐색 요청을 실행하면 후보 합금, 점수, 위험 플래그가 여기에 표시됩니다.</div>
          </div>
        </section>
      </section>
    </div>
  </main>
  <script>
    const defaultPrompt = "__DEFAULT_PROMPT__";
    const promptEl = document.getElementById("prompt");
    const samplesEl = document.getElementById("samples");
    const topEl = document.getElementById("top");
    const runBtn = document.getElementById("run");
    const resetBtn = document.getElementById("reset");
    const resultsEl = document.getElementById("results");
    const summaryEl = document.getElementById("summary");
    const statusText = document.getElementById("statusText");
    promptEl.value = defaultPrompt;

    function pct(v) { return Math.round(v * 100); }
    function scoreBar(label, value, cls) {
      const percent = pct(value);
      return `<div class="bar"><span>${label}</span><div class="track"><div class="fill ${cls}" style="width:${percent}%"></div></div><span>${percent}</span></div>`;
    }
    function renderSummary(result) {
      const top = result.top || [];
      const best = top.length ? top[0].rank_score.toFixed(1) : "-";
      const priority = top.filter(c => c.recommendation.includes("우선")).length;
      const uncertainty = top.length ? (top.reduce((sum, c) => sum + c.uncertainty, 0) / top.length).toFixed(2) : "-";
      summaryEl.innerHTML = `
        <div class="metric"><div class="metric-value">${result.generated_count}</div><div class="metric-label">생성 후보</div></div>
        <div class="metric"><div class="metric-value">${best}</div><div class="metric-label">최고 점수</div></div>
        <div class="metric"><div class="metric-value">${priority}</div><div class="metric-label">우선 검증 후보</div></div>
        <div class="metric"><div class="metric-value">${uncertainty}</div><div class="metric-label">평균 불확실성</div></div>`;
    }
    function renderResults(result) {
      if (!result.top || !result.top.length) {
        resultsEl.innerHTML = `<div class="empty">조건을 만족하는 후보가 없습니다. 원소 제한이나 밀도/융점 조건을 완화해 보세요.</div>`;
        return;
      }
      const rows = result.top.map((c, index) => {
        const composition = Object.entries(c.composition).map(([k, v]) => `<span class="tag">${k} ${v.toFixed(1)}%</span>`).join("");
        const risks = c.risk_flags.length
          ? c.risk_flags.map((r, i) => `<div class="${i > 1 ? "risk high" : "risk"}">${r}</div>`).join("")
          : `<span class="tag">주요 플래그 없음</span>`;
        const bars = `
          <div class="bars">
            ${scoreBar("연성", c.scores.ductility, "ductility")}
            ${scoreBar("고온", c.scores.high_temperature, "temp")}
            ${scoreBar("저방사", c.scores.low_activation, "activation")}
            ${scoreBar("BCC", c.scores.bcc_stability, "")}
          </div>`;
        return `<tr>
          <td>${index + 1}</td>
          <td><div class="formula">${c.formula}</div><div>${composition}</div></td>
          <td><div class="score">${c.rank_score.toFixed(2)}</div><div class="subtitle">uncertainty ${c.uncertainty.toFixed(2)}</div></td>
          <td>${bars}</td>
          <td>${c.recommendation}</td>
          <td>${risks}</td>
        </tr>`;
      }).join("");
      resultsEl.innerHTML = `
        <table>
          <thead><tr><th>#</th><th>조성</th><th>종합</th><th>주요 점수</th><th>판정</th><th>위험 플래그</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>`;
    }
    async function runScreen() {
      runBtn.disabled = true;
      statusText.textContent = "탐색 중";
      resultsEl.innerHTML = `<div class="empty">합금 후보를 생성하고 점수화하는 중입니다.</div>`;
      try {
        const response = await fetch("/api/screen", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({
            prompt: promptEl.value,
            samples: Number(samplesEl.value || 2500),
            top: Number(topEl.value || 25)
          })
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "screening failed");
        renderSummary(result);
        renderResults(result);
        statusText.textContent = "탐색 완료";
      } catch (error) {
        resultsEl.innerHTML = `<div class="empty">오류: ${error.message}</div>`;
        statusText.textContent = "오류";
      } finally {
        runBtn.disabled = false;
      }
    }
    runBtn.addEventListener("click", runScreen);
    resetBtn.addEventListener("click", () => {
      promptEl.value = defaultPrompt;
      samplesEl.value = 2500;
      topEl.value = 25;
    });
    runScreen();
  </script>
</body>
</html>""".replace("__DEFAULT_PROMPT__", DEFAULT_PROMPT.replace('"', '\\"'))


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self) -> None:
        body = INDEX_HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._send_html()
        elif path == "/api/elements":
            self._send_json({"elements": element_catalog()})
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/screen":
            self._send_json({"error": "not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            prompt = str(payload.get("prompt") or DEFAULT_PROMPT)
            samples = max(100, min(10000, int(payload.get("samples", 2500))))
            top = max(5, min(100, int(payload.get("top", 25))))
            result = screen_candidates(prompt, samples=samples, top_n=top)
            self._send_json(result)
        except Exception as exc:
            self._send_json({"error": str(exc)}, 500)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Fusion Alloy AI Screener web app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Fusion Alloy AI Screener running at http://{args.host}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
