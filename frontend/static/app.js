let currentCategory = '전체';
let searchTimer = null;

// ── 탭 전환 ──
function setTab(tab) {
  document.getElementById('tab-dashboard').style.display = tab === 'dashboard' ? 'block' : 'none';
  document.getElementById('tab-briefing').style.display = tab === 'briefing' ? 'block' : 'none';
  document.querySelectorAll('.nav-item').forEach((el, i) => {
    el.classList.toggle('active', (tab === 'dashboard' && i === 0) || (tab === 'briefing' && i === 1));
  });
  if (tab === 'briefing') loadBriefing();
}

// ── 카테고리 필터 ──
function filterCategory(cat) {
  currentCategory = cat;
  document.querySelectorAll('.cat-btn').forEach(el => {
    el.classList.toggle('active', el.textContent.includes(cat) || (cat === '전체' && el.textContent === '전체'));
  });
  loadArticles();
}

// ── 검색 (디바운스) ──
function debounceSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadArticles, 400);
}

// ── 기사 로드 ──
async function loadArticles() {
  const keyword = document.getElementById('search-input').value.trim();
  const params = new URLSearchParams({ limit: 60 });
  if (currentCategory !== '전체') params.append('category', currentCategory);
  if (keyword) params.append('keyword', keyword);

  try {
    const res = await fetch(`/api/articles?${params}`);
    const data = await res.json();
    renderArticles(data.articles);
    document.getElementById('last-updated').textContent =
      `${data.count}건 · ${new Date().toLocaleTimeString('ko-KR')} 기준`;
  } catch (e) {
    showGrid('<div class="loading">불러오기 실패</div>');
  }
}

// ── 기사 렌더링 ──
function renderArticles(articles) {
  if (!articles.length) {
    showGrid('<div class="loading">기사가 없습니다</div>');
    return;
  }
  const sentimentMap = { positive: '↑ 긍정', negative: '↓ 부정', neutral: '– 중립' };
  const html = articles.map(a => `
    <div class="news-card">
      <div class="card-header">
        <span class="card-category">${a.category || '일반'}</span>
        ${a.sentiment ? `<span class="card-sentiment ${a.sentiment}">${sentimentMap[a.sentiment] || ''}</span>` : ''}
      </div>
      <div class="card-title">
        <a href="${a.url}" target="_blank" rel="noopener">${escHtml(a.title)}</a>
      </div>
      ${a.summary
        ? `<div class="card-summary">${escHtml(a.summary)}</div>`
        : `<div class="no-summary">분석 대기 중...</div>`
      }
      <div class="card-footer">
        <span class="card-source">${escHtml(a.source || '')}</span>
        ${a.keywords ? `<span class="card-keywords">${escHtml(a.keywords)}</span>` : ''}
      </div>
    </div>
  `).join('');
  showGrid(html);
}

function showGrid(html) {
  document.getElementById('news-grid').innerHTML = html;
}

// ── 통계 로드 ──
async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    document.getElementById('stat-total').textContent = data.total;
    document.getElementById('stat-analyzed').textContent = data.analyzed;
    updateSentimentBar(data.sentiments || {});
  } catch {}
}

function updateSentimentBar(sentiments) {
  const total = Object.values(sentiments).reduce((a, b) => a + b, 0) || 1;
  const pct = k => Math.round((sentiments[k] || 0) / total * 100);
  document.getElementById('sent-positive').style.width = pct('positive') + '%';
  document.getElementById('sent-neutral').style.width = pct('neutral') + '%';
  document.getElementById('sent-negative').style.width = pct('negative') + '%';
}

// ── 브리핑 로드 ──
async function loadBriefing() {
  try {
    const res = await fetch('/api/briefing');
    const data = await res.json();
    if (data.content) {
      renderBriefing(data.content, data.created_at);
    }
  } catch {}
}

async function generateBriefing() {
  const btn = document.getElementById('btn-briefing');
  btn.disabled = true;
  btn.textContent = '생성 중...';
  document.getElementById('briefing-content').innerHTML = '<div class="briefing-empty">AI가 브리핑을 작성하고 있습니다...</div>';
  try {
    const res = await fetch('/api/briefing/generate', { method: 'POST' });
    const data = await res.json();
    renderBriefing(data.content, new Date().toISOString());
    showToast('✅ 브리핑 생성 완료');
  } catch {
    showToast('❌ 브리핑 생성 실패');
  } finally {
    btn.disabled = false;
    btn.textContent = '✨ 브리핑 생성';
  }
}

function renderBriefing(content, createdAt) {
  document.getElementById('briefing-content').innerHTML = markdownToHtml(content);
  if (createdAt) {
    document.getElementById('briefing-time').textContent =
      new Date(createdAt).toLocaleString('ko-KR') + ' 생성';
  }
}

// ── 수동 제어 ──
async function triggerCollect() {
  const btn = document.getElementById('btn-collect');
  btn.disabled = true;
  btn.textContent = '수집 중...';
  try {
    const res = await fetch('/api/collect', { method: 'POST' });
    const data = await res.json();
    showToast(`✅ ${data.saved}건 저장, ${data.analyzed}건 분석`);
    loadArticles();
    loadStats();
  } catch {
    showToast('❌ 수집 실패');
  } finally {
    btn.disabled = false;
    btn.textContent = '🔄 지금 수집';
  }
}

async function triggerAnalyze() {
  const btn = document.getElementById('btn-analyze');
  btn.disabled = true;
  btn.textContent = '분석 중...';
  try {
    const res = await fetch('/api/analyze', { method: 'POST' });
    const data = await res.json();
    showToast(`✅ ${data.analyzed}건 분석 완료`);
    loadArticles();
    loadStats();
  } catch {
    showToast('❌ 분석 실패');
  } finally {
    btn.disabled = false;
    btn.textContent = '🤖 분석 실행';
  }
}

// ── 유틸 ──
function escHtml(str) {
  return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function markdownToHtml(md) {
  return md
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(?!<[hul])/gm, '')
    .replace(/(<p><\/p>)/g, '');
}

let toastTimer;
function showToast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 3000);
}

// ── 초기화 ──
loadArticles();
loadStats();
// 1분마다 자동 갱신
setInterval(() => { loadArticles(); loadStats(); }, 60000);
