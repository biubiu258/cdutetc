const resultOutput = document.getElementById("result-output");
const userInfoStatus = document.getElementById("user-info-status");
const timetableStatus = document.getElementById("timetable-refresh-status");
const scoreStatus = document.getElementById("score-init-status");

const setStatus = (element, text, isSuccess = true) => {
  element.textContent = text;
  element.style.color = isSuccess ? "#12b76a" : "#f04438";
};

const updateResult = (title, payload) => {
  const content = payload === undefined ? "" : JSON.stringify(payload, null, 2);
  resultOutput.textContent = `${title}\n\n${content}`;
};

const safeParseJson = async (response) => {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch (error) {
    return { raw: text };
  }
};

const requestApi = async (url, options = {}) => {
  const response = await fetch(url, options);
  const data = await safeParseJson(response);
  if (!response.ok) {
    throw new Error(data?.message || `请求失败：${response.status}`);
  }
  return data;
};

const handleError = (action, error) => {
  updateResult(`${action}失败`, { message: error.message });
};

const handleResult = (action, data) => {
  updateResult(`${action}完成`, data);
};

const bindAction = (selector, handler) => {
  document.querySelectorAll(selector).forEach((element) => {
    element.addEventListener("click", handler);
  });
};

bindAction("[data-action='check-user-info']", async () => {
  try {
    const data = await requestApi("/api/is_has_user_info");
    const status = data?.data ? "已配置" : "未配置";
    setStatus(userInfoStatus, status, data?.data);
    handleResult("检查账号状态", data);
  } catch (error) {
    setStatus(userInfoStatus, "异常", false);
    handleError("检查账号状态", error);
  }
});

bindAction("[data-action='auto-login']", async () => {
  try {
    const data = await requestApi("/api/login");
    handleResult("自动登录", data);
  } catch (error) {
    handleError("自动登录", error);
  }
});

document.querySelector("[data-form='login']").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.target);
  try {
    const data = await requestApi("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: formData.get("username"),
        password: formData.get("password"),
      }),
    });
    handleResult("登录", data);
  } catch (error) {
    handleError("登录", error);
  }
});

document.querySelector("[data-form='user-info']").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.target);
  try {
    const data = await requestApi("/api/change_user_info", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: formData.get("username"),
        password: formData.get("password"),
        email_sender: formData.get("email_sender"),
        email_password: formData.get("email_password"),
        email_to: formData.get("email_to"),
      }),
    });
    setStatus(userInfoStatus, "已更新", true);
    handleResult("保存用户信息", data);
  } catch (error) {
    handleError("保存用户信息", error);
  }
});

bindAction("[data-action='enable-email']", async () => {
  try {
    const data = await requestApi("/score/enable_email");
    handleResult("启用邮件通知", data);
  } catch (error) {
    handleError("启用邮件通知", error);
  }
});

bindAction("[data-action='disable-email']", async () => {
  try {
    const data = await requestApi("/score/disable_email");
    handleResult("关闭邮件通知", data);
  } catch (error) {
    handleError("关闭邮件通知", error);
  }
});

bindAction("[data-action='refresh-timetable']", async () => {
  try {
    const data = await requestApi("/timetable/refresh_timetable");
    setStatus(timetableStatus, "已刷新", true);
    handleResult("刷新课表", data);
  } catch (error) {
    setStatus(timetableStatus, "失败", false);
    handleError("刷新课表", error);
  }
});

bindAction("[data-action='get-everyday']", async () => {
  try {
    const data = await requestApi("/timetable/timetable");
    handleResult("完整课表", data);
  } catch (error) {
    handleError("完整课表", error);
  }
});

bindAction("[data-action='get-today']", async () => {
  try {
    const data = await requestApi("/timetable/today_class");
    handleResult("今日课程", data);
  } catch (error) {
    handleError("今日课程", error);
  }
});

bindAction("[data-action='get-now']", async () => {
  try {
    const data = await requestApi("/timetable/get_now_class");
    handleResult("当前课程", data);
  } catch (error) {
    handleError("当前课程", error);
  }
});

document.querySelector("[data-form='class-after-days']").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.target);
  try {
    const days = formData.get("days");
    const data = await requestApi(`/timetable/get_class_after_days?days=${encodeURIComponent(days)}`);
    handleResult(`查询${days}天后课程`, data);
  } catch (error) {
    handleError("查询几天后课程", error);
  }
});

document.querySelector("[data-form='class-by-date']").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.target);
  try {
    const date = formData.get("date");
    const data = await requestApi(`/timetable/get_str_date_class?date=${encodeURIComponent(date)}`);
    handleResult(`查询${date}课程`, data);
  } catch (error) {
    handleError("查询指定日期课程", error);
  }
});

document.querySelector("[data-form='class-by-text']").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.target);
  try {
    const text = formData.get("text");
    const data = await requestApi(`/timetable/get_class_by_text?text=${encodeURIComponent(text)}`);
    handleResult(`智能查询：${text}`, data);
  } catch (error) {
    handleError("智能查询课程", error);
  }
});

bindAction("[data-action='score-init']", async () => {
  try {
    const data = await requestApi("/score/init");
    setStatus(scoreStatus, "已初始化", true);
    handleResult("初始化成绩", data);
  } catch (error) {
    setStatus(scoreStatus, "失败", false);
    handleError("初始化成绩", error);
  }
});

bindAction("[data-action='score-update']", async () => {
  try {
    const data = await requestApi("/score/update");
    handleResult("更新成绩数据", data);
  } catch (error) {
    handleError("更新成绩数据", error);
  }
});

bindAction("[data-action='score-all']", async () => {
  try {
    const data = await requestApi("/score/all_score");
    handleResult("历史成绩", data);
  } catch (error) {
    handleError("历史成绩", error);
  }
});

bindAction("[data-action='score-semester']", async () => {
  try {
    const data = await requestApi("/score/query_this_semester");
    handleResult("本学期成绩", data);
  } catch (error) {
    handleError("本学期成绩", error);
  }
});

bindAction("[data-action='score-credits']", async () => {
  try {
    const data = await requestApi("/score/accumulate_history_credits");
    handleResult("累计学分统计", data);
  } catch (error) {
    handleError("累计学分统计", error);
  }
});

bindAction("[data-action='score-retake']", async () => {
  try {
    const data = await requestApi("/score/query_retake_total_paid");
    handleResult("重修缴费统计", data);
  } catch (error) {
    handleError("重修缴费统计", error);
  }
});

bindAction("[data-action='clear-result']", () => {
  resultOutput.textContent = "等待操作...";
});

const disclaimerModal = document.getElementById("disclaimer-modal");
const disclaimerKey = "cdutetc-disclaimer-accepted";

const showDisclaimer = () => {
  disclaimerModal.classList.add("active");
  disclaimerModal.setAttribute("aria-hidden", "false");
};

const hideDisclaimer = () => {
  disclaimerModal.classList.remove("active");
  disclaimerModal.setAttribute("aria-hidden", "true");
};

if (!localStorage.getItem(disclaimerKey)) {
  showDisclaimer();
}

bindAction("[data-action='accept-disclaimer']", () => {
  localStorage.setItem(disclaimerKey, "true");
  hideDisclaimer();
});
