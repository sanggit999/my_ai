/**
 * Multi-AI Studio Dashboard — Client Application Logic (Phase 11 / Option C).
 */

let currentStages = {};
let latestResult = null;
let currentTab = 'final';

document.addEventListener('DOMContentLoaded', () => {
  fetchStatus();
  fetchStages();

  document.getElementById('btnRefreshStatus').addEventListener('click', () => {
    fetchStatus();
    fetchStages();
  });

  document.getElementById('btnRunPipeline').addEventListener('click', runPipeline);
  document.getElementById('btnOpenSetupModal').addEventListener('click', openSetupModal);

  // Ctrl + Enter to submit prompt
  document.getElementById('promptInput').addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      runPipeline();
    }
  });
});

/* ==============================================================================
   API FETCH & STATUS
   ============================================================================== */
async function fetchStatus() {
  try {
    const res = await fetch('/api/status');
    const data = await res.json();
    if (data.status === 'ok') {
      const p = data.providers;
      updateBadge('groq', 'Groq', p.groq);
      updateBadge('gemini', 'Gemini', p.gemini);
      updateBadge('openai', 'OpenAI', p.openai);
      updateBadge('anthropic', 'Claude', p.anthropic);
    }
  } catch (err) {
    console.error('Lỗi nạp status:', err);
  }
}

function updateBadge(id, name, info) {
  const el = document.getElementById(`badge-${id}`);
  if (!el || !info) return;

  if (info.is_ready) {
    el.className = 'status-badge ready';
    el.innerHTML = `<span class="dot"></span> ${name}: ${info.active_model}`;
    el.title = `API Sẵn sàng (${info.masked_key})`;
  } else {
    el.className = 'status-badge error';
    el.innerHTML = `<span class="dot"></span> ${name}: Thiếu key`;
    el.title = 'Chưa cấu hình API Key';
  }
}

async function fetchStages() {
  try {
    const res = await fetch('/api/stages');
    const data = await res.json();
    if (data.status === 'ok') {
      currentStages = data.stages;
      renderFlowNodes();
    }
  } catch (err) {
    console.error('Lỗi nạp stages:', err);
  }
}

function renderFlowNodes() {
  if (!currentStages) return;

  const h = currentStages.head || {};
  const b = currentStages.body || {};
  const t = currentStages.tail || {};

  document.getElementById('label-head-model').innerText = `${h.provider || 'groq'} : ${h.model || ''}`;
  document.getElementById('label-body-model').innerText = `${b.provider || 'gemini'} : ${b.model || ''}`;
  document.getElementById('label-tail-model').innerText = `${t.provider || 'groq'} : ${t.model || ''}`;
}

/* ==============================================================================
   PIPELINE EXECUTION
   ============================================================================== */
async function runPipeline() {
  const prompt = document.getElementById('promptInput').value.trim();
  if (!prompt) {
    alert('Vui lòng nhập nội dung yêu cầu hoặc câu hỏi trước khi vận hành dây chuyền.');
    return;
  }

  const runBtn = document.getElementById('btnRunPipeline');
  runBtn.disabled = true;
  runBtn.innerHTML = '<span class="btn-icon">⏳</span> ĐANG VẬN HÀNH...';

  // Reset visual state
  document.getElementById('failoverBanner').style.display = 'none';
  document.getElementById('telemetryBar').style.display = 'none';
  resetNodeStyles();

  setNodeState('node-head', 'active-running', 'Đang xử lý...');
  setNodeState('node-body', '', 'Chờ chặng 1...');
  setNodeState('node-tail', '', 'Chờ chặng 2...');
  setNodeState('node-final', '', 'Đang xử lý...');

  document.getElementById('tabContent').innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">⚙️</div>
      <div class="empty-title">Dây Chuyền Đang Hoạt Động</div>
      <div class="empty-desc">Chặng 1 (ĐẦU) đang bóc tách kiến trúc. Nếu có sự cố, cơ chế Active-Survivor sẽ tự điều động AI còn sống nhảy vào thay thế ngay lập tức...</div>
    </div>
  `;

  try {
    const startTime = performance.now();
    const res = await fetch('/api/pipeline/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
    });

    const data = await res.json();
    const totalTime = ((performance.now() - startTime) / 1000).toFixed(2);

    if (data.status === 'ok') {
      latestResult = data;
      renderPipelineSuccess(data, totalTime);
    } else {
      alert(`Lỗi thực thi dây chuyền: ${data.message || 'Không rõ lỗi'}`);
      resetNodeStyles();
    }
  } catch (err) {
    alert(`Lỗi kết nối tới máy chủ: ${err.message}`);
    resetNodeStyles();
  } finally {
    runBtn.disabled = false;
    runBtn.innerHTML = '<span class="btn-icon">⚡</span> VẬN HÀNH DÂY CHUYỀN';
  }
}

function renderPipelineSuccess(data, totalTime) {
  // Update node statuses
  data.stages.forEach((st) => {
    const nodeElId = `node-${st.stage_key}`;
    if (st.is_failover) {
      setNodeState(
        nodeElId,
        'active-failover',
        `🚨 Đã Cứu Hộ: ${st.executed_provider.toUpperCase()}`
      );
    } else {
      setNodeState(
        nodeElId,
        'active-success',
        `✅ Hoàn tất (${(st.latency_ms / 1000).toFixed(2)}s)`
      );
    }
  });

  setNodeState('node-final', 'active-success', 'Hoàn tất xuất bản');

  // Handle failover banner
  if (data.failovers_occurred > 0) {
    const banner = document.getElementById('failoverBanner');
    banner.style.display = 'flex';
    const failedStages = data.stages
      .filter((s) => s.is_failover)
      .map(
        (s) =>
          `[${s.stage_name}]: ${s.assigned_provider.toUpperCase()} lỗi (${s.failover_reason || 'Sự cố'}) ➔ ${s.executed_provider.toUpperCase()} (${s.executed_model}) đã nhảy vào gánh thành công!`
      )
      .join('<br>');

    document.getElementById('failoverDesc').innerHTML = failedStages;
  }

  // Telemetry
  const tele = document.getElementById('telemetryBar');
  tele.style.display = 'flex';
  document.getElementById('tLatency').innerText = `${(data.total_latency_ms / 1000).toFixed(2)} s`;
  document.getElementById('tFailovers').innerText = `${data.failovers_occurred} lần cứu hộ`;

  // Render Result Tab
  switchTab(currentTab);
}

function resetNodeStyles() {
  ['node-head', 'node-body', 'node-tail', 'node-final'].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.className = el.className.replace(/active-\w+/g, '').trim();
  });
}

function setNodeState(nodeId, stateClass, statusText) {
  const el = document.getElementById(nodeId);
  if (!el) return;
  el.className = `flow-node ${stateClass}`.trim();
  const statusEl = el.querySelector('.node-status');
  if (statusEl && statusText) statusEl.innerText = statusText;
}

/* ==============================================================================
   TABS & MARKDOWN RENDERING
   ============================================================================== */
function switchTab(tabKey) {
  currentTab = tabKey;
  document.querySelectorAll('.tab-btn').forEach((btn) => {
    btn.classList.remove('active');
  });

  // Activate tab button
  const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find((b) =>
    b.getAttribute('onclick')?.includes(`'${tabKey}'`)
  );
  if (activeBtn) activeBtn.classList.add('active');

  const container = document.getElementById('tabContent');
  if (!latestResult) return;

  if (tabKey === 'final') {
    container.innerHTML = `
      <div class="markdown-body">
        ${renderMarkdownHTML(latestResult.final_content)}
      </div>
    `;
  } else if (['head', 'body', 'tail'].includes(tabKey)) {
    const st = latestResult.stages.find((s) => s.stage_key === tabKey);
    if (st) {
      const badge = st.is_failover
        ? `<div class="failover-alert-banner" style="margin-bottom: 16px;">
             <div class="alert-icon">🚨</div>
             <div>
               <strong>Cơ chế tự phục hồi kích hoạt:</strong> Con chỉ định ban đầu (${st.assigned_provider.toUpperCase()}) gặp sự cố (${st.failover_reason || 'Lỗi'}). 
               AI cứu hộ <strong>${st.executed_provider.toUpperCase()} (${st.executed_model})</strong> đã nhảy vào gánh thành công trong ${(st.latency_ms / 1000).toFixed(2)}s!
             </div>
           </div>`
        : '';
      container.innerHTML = `
        ${badge}
        <div class="markdown-body">
          ${renderMarkdownHTML(st.output_content)}
        </div>
      `;
    }
  } else if (tabKey === 'events') {
    let rows = (latestResult.events || [])
      .map(
        (ev) => `
        <tr>
          <td><strong>${ev.stage_name}</strong></td>
          <td><span class="badge">${ev.provider.toUpperCase()}</span></td>
          <td>${ev.status}</td>
          <td>${new Date(ev.timestamp * 1000).toLocaleTimeString()}</td>
        </tr>
      `
      )
      .join('');

    container.innerHTML = `
      <table class="events-table">
        <thead>
          <tr>
            <th>Chặng</th>
            <th>Nhà Cung Cấp</th>
            <th>Trạng Thái / Diễn Biến</th>
            <th>Thời Điểm</th>
          </tr>
        </thead>
        <tbody>
          ${rows || '<tr><td colspan="4">Chưa có nhật ký sự kiện.</td></tr>'}
        </tbody>
      </table>
    `;
  }
}

function renderMarkdownHTML(md) {
  if (!md) return '<p>Chưa có nội dung.</p>';

  // Simple, resilient markdown renderer
  let html = md
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Fenced code blocks
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre><div style="position: absolute; top: 8px; right: 12px; font-size: 11px; color: #94a3b8; font-weight: 600;">${lang.toUpperCase() || 'CODE'}</div><code>${code.trim()}</code></pre>`;
  });

  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

  // Bold & Italic
  html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>');

  // Blockquotes
  html = html.replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>');

  // Unordered lists
  html = html.replace(/^\s*[-*]\s+(.*$)/gim, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/gims, '<ul>$1</ul>');

  // Paragraphs
  html = html.replace(/\n\n/g, '</p><p>');
  html = `<p>${html}</p>`;

  return html;
}

function setPrompt(text) {
  document.getElementById('promptInput').value = text;
}

function copyCurrentOutput() {
  if (!latestResult) return;
  let textToCopy = '';
  if (currentTab === 'final') {
    textToCopy = latestResult.final_content;
  } else {
    const st = latestResult.stages.find((s) => s.stage_key === currentTab);
    textToCopy = st ? st.output_content : '';
  }

  if (textToCopy) {
    navigator.clipboard.writeText(textToCopy).then(() => {
      const btn = document.getElementById('btnCopyResult');
      btn.innerText = '✅ Đã sao chép!';
      setTimeout(() => {
        btn.innerText = '📋 Sao chép';
      }, 2000);
    });
  }
}

/* ==============================================================================
   SETUP MODAL
   ============================================================================== */
function openSetupModal() {
  if (!currentStages) return;

  const h = currentStages.head || {};
  const b = currentStages.body || {};
  const t = currentStages.tail || {};

  document.getElementById('cfg-head-provider').value = h.provider || 'groq';
  document.getElementById('cfg-head-model').value = h.model || '';

  document.getElementById('cfg-body-provider').value = b.provider || 'gemini';
  document.getElementById('cfg-body-model').value = b.model || '';

  document.getElementById('cfg-tail-provider').value = t.provider || 'groq';
  document.getElementById('cfg-tail-model').value = t.model || '';

  document.getElementById('setupModal').style.display = 'flex';
}

function openStageSetup(stageKey) {
  openSetupModal();
}

function closeSetupModal() {
  document.getElementById('setupModal').style.display = 'none';
}

function onProviderChange(stageKey) {
  const p = document.getElementById(`cfg-${stageKey}-provider`).value;
  const inputEl = document.getElementById(`cfg-${stageKey}-model`);
  const defaultModels = {
    groq: 'openai/gpt-oss-120b',
    gemini: 'gemini-3.1-flash-lite',
    openai: 'gpt-4o-mini',
    anthropic: 'claude-3-5-haiku-20241022',
  };
  inputEl.value = defaultModels[p] || '';
}

async function saveStageConfig() {
  const stagesToSave = [
    {
      key: 'head',
      p: document.getElementById('cfg-head-provider').value,
      m: document.getElementById('cfg-head-model').value.trim(),
    },
    {
      key: 'body',
      p: document.getElementById('cfg-body-provider').value,
      m: document.getElementById('cfg-body-model').value.trim(),
    },
    {
      key: 'tail',
      p: document.getElementById('cfg-tail-provider').value,
      m: document.getElementById('cfg-tail-model').value.trim(),
    },
  ];

  for (const s of stagesToSave) {
    await fetch('/api/stages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stage_key: s.key, provider: s.p, model: s.m }),
    });
  }

  await fetchStages();
  closeSetupModal();
  alert('Đã lưu cấu hình 3 chặng thành công!');
}

async function resetToDefaultStages() {
  if (confirm('Khôi phục cấu hình 3 chặng về mặc định ban đầu?')) {
    await fetch('/api/stages/reset', { method: 'POST' });
    await fetchStages();
    openSetupModal();
  }
}
