const RESULT_STATES = {
  idle: { label: '等待操作', status: 'idle' },
  loading: { label: '正在请求...', status: 'warning' },
  success: { label: '请求成功', status: 'success' },
  error: { label: '请求失败', status: 'error' },
};

const escapeHTML = (value) =>
  String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

const renderPanelState = (panel, stateKey, message) => {
  const status = panel.querySelector('.status');
  const msg = panel.querySelector('.result-msg');
  const body = panel.querySelector('.result-body');
  const state = RESULT_STATES[stateKey];
  status.dataset.status = state.status;
  msg.textContent = message || state.label;
  if (stateKey === 'loading') {
    body.innerHTML = '<p class="muted">正在加载数据，请稍候...</p>';
  }
};

const setLoginState = (isLoggedIn) => {
  const statusBox = document.getElementById('login-status-box');
  const status = statusBox.querySelector('.status');
  const msg = statusBox.querySelector('.result-msg');
  status.dataset.status = isLoggedIn ? 'success' : 'warning';
  status.textContent = isLoggedIn ? '已登录' : '未登录';
  msg.textContent = isLoggedIn ? '已解锁全部功能模块。' : '请先完成登录后再继续。';
  document.querySelectorAll('.tab').forEach((tab) => {
    if (tab.dataset.tab === 'login') {
      return;
    }
    tab.disabled = !isLoggedIn;
  });
};

const setGlobalLoading = (isLoading) => {
  const loader = document.getElementById('global-loader');
  document.body.classList.toggle('is-loading', isLoading);
  loader.classList.toggle('show', isLoading);
  loader.setAttribute('aria-hidden', String(!isLoading));
  toggleControls(!isLoading);
};

const toggleControls = (enabled) => {
  document
    .querySelectorAll('button, input, select, textarea')
    .forEach((element) => {
      element.disabled = !enabled;
    });
};

const renderData = (data) => {
  if (data === null || data === undefined) {
    return '<p class="muted">暂无数据。</p>';
  }
  if (typeof data === 'string') {
    return `<p>${escapeHTML(data)}</p>`;
  }
  if (Array.isArray(data)) {
    if (data.length === 0) {
      return '<p class="muted">暂无记录。</p>';
    }
    if (isTimetableList(data)) {
      return renderTimetableList(data);
    }
    if (isSemesterScoreList(data)) {
      return renderSemesterScores(data);
    }
    if (isGradeHistoryList(data)) {
      return renderGradeHistory(data);
    }
    if (isRetakeList(data)) {
      return renderRetakeList(data);
    }
    return renderGenericList(data);
  }
  if (typeof data === 'object') {
    if (isTimetableMap(data)) {
      return renderTimetableCalendar(data);
    }
    if (isRetakeSummary(data)) {
      return renderRetakeSummary(data);
    }
    if (isCreditSummary(data)) {
      return renderCreditSummary(data);
    }
    return renderObjectGrid(data);
  }
  return `<pre>${escapeHTML(JSON.stringify(data, null, 2))}</pre>`;
};

const renderGenericList = (items) => {
  return `
    <table class="list-table">
      <thead>
        <tr>
          <th>#</th>
          <th>内容</th>
        </tr>
      </thead>
      <tbody>
        ${items
          .map(
            (item, index) => `
              <tr>
                <td>${index + 1}</td>
                <td>${escapeHTML(JSON.stringify(item))}</td>
              </tr>
            `,
          )
          .join('')}
      </tbody>
    </table>
  `;
};

const renderObjectGrid = (obj) => {
  return `
    <div class="data-grid">
      ${Object.entries(obj)
        .map(
          ([key, value]) => `
            <div class="data-card">
              <h4>${escapeHTML(key)}</h4>
              <div class="muted">${escapeHTML(formatValue(value))}</div>
            </div>
          `,
        )
        .join('')}
    </div>
  `;
};

const formatValue = (value) => {
  if (Array.isArray(value)) {
    return `${value.length} 项`;
  }
  if (typeof value === 'object' && value !== null) {
    return '详情请展开查看';
  }
  return String(value);
};

const isTimetableList = (items) => items.every((item) => item && 'name' in item && 'sequence' in item);

const isTimetableMap = (obj) =>
  Object.entries(obj).some(
    ([key, value]) =>
      /^\d{4}-\d{2}-\d{2}$/.test(key) &&
      Array.isArray(value) &&
      value.some((item) => item && 'name' in item && 'sequence' in item),
  );

const renderTimetableList = (items) => {
  return `
    <div class="data-grid">
      ${items
        .map(
          (item) => `
            <div class="data-card">
              <h4>${escapeHTML(item.name || '未知课程')}</h4>
              <div class="muted">教室：${escapeHTML(item.classroom || '未知')}</div>
              <div class="muted">节次：${escapeHTML(item.sequence?.join('-') || '')}</div>
              <div class="muted">教师：${escapeHTML(item.teacher || '未知')}</div>
              <div class="badge">${escapeHTML(item.method || '未知考核')}</div>
            </div>
          `,
        )
        .join('')}
    </div>
  `;
};

const renderTimetableCalendar = (map) => {
  const grouped = groupByMonth(map);
  return Object.entries(grouped)
    .map(([monthKey, monthData]) => renderMonthCalendar(monthKey, monthData))
    .join('');
};

const groupByMonth = (map) => {
  return Object.entries(map).reduce((acc, [dateStr, classes]) => {
    const date = new Date(dateStr);
    if (Number.isNaN(date.getTime())) {
      return acc;
    }
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    acc[key] = acc[key] || {};
    acc[key][dateStr] = classes;
    return acc;
  }, {});
};

const renderMonthCalendar = (monthKey, data) => {
  const [year, month] = monthKey.split('-').map(Number);
  const firstDay = new Date(year, month - 1, 1);
  const lastDay = new Date(year, month, 0);
  const startWeekday = firstDay.getDay();
  const daysInMonth = lastDay.getDate();
  const weekLabels = ['日', '一', '二', '三', '四', '五', '六'];
  const cells = [];

  for (let i = 0; i < startWeekday; i += 1) {
    cells.push('<div class="calendar-cell empty"></div>');
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    const date = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const classes = data[date] || [];
    const items = classes
      .map(
        (item) => `
          <div class="calendar-item">
            ${escapeHTML(item.name || '未知课程')}<br />
            <span class="muted">${escapeHTML(item.classroom || '未知')}</span>
          </div>
        `,
      )
      .join('');
    cells.push(`
      <div class="calendar-cell">
        <div class="calendar-date">${day}</div>
        ${items || '<div class="muted">无课程</div>'}
      </div>
    `);
  }

  return `
    <div class="calendar">
      <div class="calendar-header">
        <h4>${year}年 ${month}月</h4>
      </div>
      <div class="calendar-grid">
        ${weekLabels.map((label) => `<div class="calendar-date">${label}</div>`).join('')}
        ${cells.join('')}
      </div>
    </div>
  `;
};

const isGradeHistoryList = (items) =>
  items.some((item) => item && (item.course_name || item.kcmc || item.max_grade !== undefined));

const isSemesterScoreList = (items) =>
  items.some((item) => item && item.course_name && item.academic_year && item.grade !== undefined);

const renderGradeHistory = (items) => {
  return `
    <div class="data-grid">
      ${items
        .map((item) => {
          const name = item.course_name || item.kcmc || '未知课程';
          const grade = item.max_grade ?? item.cj ?? '暂无';
          const credits = item.max_credits ?? item.xf ?? '未知';
          const isFailed = item.is_passed === false || (typeof grade === 'number' && grade < 60);
          const statusText = isFailed ? '未通过' : '已通过';
          return `
            <div class="data-card ${isFailed ? 'failed' : ''}">
              <h4>${escapeHTML(name)}</h4>
              <div class="muted">最高成绩：<span class="${isFailed ? 'failed-text' : ''}">${escapeHTML(
                grade,
              )}</span></div>
              <div class="muted">学分：${escapeHTML(credits)}</div>
              <div class="badge">${escapeHTML(statusText)}</div>
            </div>
          `;
        })
        .join('')}
    </div>
  `;
};

const renderSemesterScores = (items) => {
  return `
    <div class="data-grid">
      ${items
        .map((item) => {
          const isFailed = item.grade < 60 || item.is_grade_invalid;
          return `
            <div class="data-card ${isFailed ? 'failed' : ''}">
              <h4>${escapeHTML(item.course_name || '未知课程')}</h4>
              <div class="muted">学年：${escapeHTML(item.academic_year)} 学期：${escapeHTML(
                item.semester,
              )}</div>
              <div class="muted">学分：${escapeHTML(item.credits)} | 绩点：${escapeHTML(item.gpa)}</div>
              <div class="muted">教师：${escapeHTML(item.instructor || '未知')}</div>
              <div class="muted">考核：${escapeHTML(item.assessment_method || '未知')}</div>
              <div class="muted">成绩：<span class="${isFailed ? 'failed-text' : ''}">${escapeHTML(
                item.grade,
              )}</span></div>
              <div class="badge">${escapeHTML(item.grade_type || '正常考试')}</div>
            </div>
          `;
        })
        .join('')}
    </div>
  `;
};

const isRetakeSummary = (data) => data && 'total_retake_paid' in data && Array.isArray(data.items);

const isRetakeList = (items) => items.some((item) => item && item.order_name && item.order_amount);

const renderRetakeSummary = (data) => {
  const items = Array.isArray(data.items) ? data.items : [];
  return `
    <div class="data-card">
      <h4>重修缴费总额</h4>
      <div class="muted">¥ ${escapeHTML(data.total_retake_paid)}</div>
    </div>
    ${items.length ? renderRetakeList(items) : '<p class="muted">暂无缴费记录。</p>'}
  `;
};

const renderRetakeList = (items) => {
  return `
    <table class="list-table">
      <thead>
        <tr>
          <th>课程</th>
          <th>金额</th>
          <th>日期</th>
          <th>状态</th>
        </tr>
      </thead>
      <tbody>
        ${items
          .map(
            (item) => `
              <tr>
                <td>${escapeHTML(item.order_name || '未知')}</td>
                <td>¥ ${escapeHTML(item.order_amount || '0')}</td>
                <td>${escapeHTML(item.pay_time|| item.dateDigit || '')}</td>
                <td>${escapeHTML(item.sfqr || item.pay_state || '')}</td>
              </tr>
            `,
          )
          .join('')}
      </tbody>
    </table>
  `;
};

const isCreditSummary = (data) =>
  data && 'total' in data && 'failed' in data && 'succeeded' in data && 'total_failed' in data;

const renderCreditSummary = (data) => {
  return `
    <div class="data-grid">
      <div class="data-card">
        <h4>总学分</h4>
        <div class="muted">${escapeHTML(data.total)}</div>
      </div>
      <div class="data-card">
        <h4>已通过</h4>
        <div class="muted">${escapeHTML(data.succeeded)}</div>
      </div>
      <div class="data-card">
        <h4>未通过</h4>
        <div class="muted">${escapeHTML(data.failed)}</div>
      </div>
      <div class="data-card">
        <h4>曾挂科学分</h4>
        <div class="muted">${escapeHTML(data.total_failed)}</div>
      </div>
    </div>
  `;
};

const requestJSON = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const payload = await response.json();
  return payload;
};

const handleAction = async (panelId, action, options = {}) => {
  if (options.requiresLogin && !window.sessionStorage.getItem('cdutetc_logged_in')) {
    const panel = document.getElementById(panelId);
    renderPanelState(panel, 'error', '请先登录后再操作');
    panel.querySelector('.result-body').innerHTML = '<p class="muted">当前未登录。</p>';
    return;
  }
  const panel = document.getElementById(panelId);
  renderPanelState(panel, 'loading');
  setGlobalLoading(true);
  try {
    const payload = await action();
    const isSuccess = payload.code === 200;
    renderPanelState(panel, isSuccess ? 'success' : 'error', payload.msg);
    panel.querySelector('.result-body').innerHTML = renderData(payload.data);
    if (options.updateLoginState && isSuccess) {
      window.sessionStorage.setItem('cdutetc_logged_in', 'true');
      setLoginState(true);
      activateTab('timetable');
    }
  } catch (error) {
    renderPanelState(panel, 'error', '请求异常，请稍后再试');
    panel.querySelector('.result-body').innerHTML = `<p class="muted">${escapeHTML(error.message)}</p>`;
  } finally {
    setGlobalLoading(false);
  }
};

const activateTab = (tabName) => {
  document.querySelectorAll('.tab').forEach((tab) => {
    const isSelected = tab.dataset.tab === tabName;
    tab.setAttribute('aria-selected', String(isSelected));
  });
  document.querySelectorAll('.tab-page').forEach((page) => {
    const isTarget = page.dataset.page === tabName;
    page.hidden = !isTarget;
  });
  if (tabName === 'timetable') {
    handleAction('timetable-result', () => requestJSON('/timetable/timetable'), {
      requiresLogin: true,
    });
  }
  if (tabName === 'score') {
    handleAction('score-result', () => requestJSON('/score/query_this_semester'), {
      requiresLogin: true,
    });
  }
};

const bindTabs = () => {
  document.querySelectorAll('.tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      if (tab.disabled) {
        return;
      }
      activateTab(tab.dataset.tab);
    });
  });
};

const bindActions = () => {
  document.getElementById('btn-check-login').addEventListener('click', () =>
    handleAction('account-result', () => requestJSON('/api/is_has_user_info')),
  );

  document.getElementById('btn-login-local').addEventListener('click', () =>
    handleAction(
      'account-result',
      () => requestJSON('/api/login'),
      { updateLoginState: true },
    ),
  );

  document.getElementById('login-form').addEventListener('submit', (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    const body = Object.fromEntries(formData.entries());
    handleAction(
      'account-result',
      () =>
        requestJSON('/api/login', {
          method: 'POST',
          body: JSON.stringify(body),
        }),
      { updateLoginState: true },
    );
  });

  document.getElementById('user-info-form').addEventListener('submit', (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    const body = Object.fromEntries(formData.entries());
    handleAction(
      'account-result',
      () =>
        requestJSON('/api/change_user_info', {
          method: 'POST',
          body: JSON.stringify(body),
        }),
      { requiresLogin: true },
    );
  });

  document.getElementById('btn-enable-email').addEventListener('click', () =>
    handleAction('account-result', () => requestJSON('/score/enable_email'), {
      requiresLogin: true,
    }),
  );

  document.getElementById('btn-disable-email').addEventListener('click', () =>
    handleAction('account-result', () => requestJSON('/score/disable_email'), {
      requiresLogin: true,
    }),
  );

  document.getElementById('btn-timetable').addEventListener('click', () =>
    handleAction('timetable-result', () => requestJSON('/timetable/timetable'), {
      requiresLogin: true,
    }),
  );

  document.getElementById('btn-today').addEventListener('click', () =>
    handleAction('timetable-result', () => requestJSON('/timetable/today_class'), {
      requiresLogin: true,
    }),
  );

  document.getElementById('btn-now').addEventListener('click', () =>
    handleAction('timetable-result', () => requestJSON('/timetable/get_now_class'), {
      requiresLogin: true,
    }),
  );

  document.getElementById('btn-refresh').addEventListener('click', () =>
    handleAction('timetable-result', () => requestJSON('/timetable/refresh_timetable'), {
      requiresLogin: true,
    }),
  );

  document.getElementById('btn-days').addEventListener('click', () => {
    const days = document.getElementById('days-input').value || 0;
    handleAction(
      'timetable-result',
      () => requestJSON(`/timetable/get_class_after_days?days=${encodeURIComponent(days)}`),
      { requiresLogin: true },
    );
  });

  document.getElementById('btn-date').addEventListener('click', () => {
    const date = document.getElementById('date-input').value;
    if (!date) {
      handleAction('timetable-result', () =>
        Promise.resolve({ code: 201, msg: '请先选择日期', data: null }),
      );
      return;
    }
    handleAction(
      'timetable-result',
      () => requestJSON(`/timetable/get_str_date_class?date=${encodeURIComponent(date)}`),
      { requiresLogin: true },
    );
  });

  document.getElementById('btn-text').addEventListener('click', () => {
    const text = document.getElementById('text-input').value.trim();
    if (!text) {
      handleAction('timetable-result', () =>
        Promise.resolve({ code: 201, msg: '请输入文本描述', data: null }),
      );
      return;
    }
    handleAction(
      'timetable-result',
      () => requestJSON(`/timetable/get_class_by_text?text=${encodeURIComponent(text)}`),
      { requiresLogin: true },
    );
  });

  document.getElementById('btn-score-all').addEventListener('click', () =>
    handleAction('score-result', () => requestJSON('/score/all_score'), { requiresLogin: true }),
  );

  document.getElementById('btn-score-semester').addEventListener('click', () =>
    handleAction('score-result', () => requestJSON('/score/query_this_semester'), {
      requiresLogin: true,
    }),
  );

  document.getElementById('btn-score-update').addEventListener('click', () =>
    handleAction('score-result', () => requestJSON('/score/update'), { requiresLogin: true }),
  );

  document.getElementById('btn-score-credits').addEventListener('click', () =>
    handleAction('score-result', () => requestJSON('/score/accumulate_history_credits'), {
      requiresLogin: true,
    }),
  );

  document.getElementById('btn-score-retake').addEventListener('click', () =>
    handleAction('score-result', () => requestJSON('/score/query_retake_total_paid'), {
      requiresLogin: true,
    }),
  );
};

const setupDisclaimer = () => {
  const modal = document.getElementById('disclaimer-modal');
  const acceptButton = document.getElementById('btn-accept');
  const hasAccepted = localStorage.getItem('cdutetc_disclaimer_accepted');
  if (!hasAccepted) {
    modal.classList.add('show');
    modal.setAttribute('aria-hidden', 'false');
  }
  acceptButton.addEventListener('click', () => {
    localStorage.setItem('cdutetc_disclaimer_accepted', 'true');
    modal.classList.remove('show');
    modal.setAttribute('aria-hidden', 'true');
  });
};

setLoginState(Boolean(window.sessionStorage.getItem('cdutetc_logged_in')));
activateTab('login');
bindTabs();
bindActions();
setupDisclaimer();