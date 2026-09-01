/**
 * BOTTERNA V2 - FRONTEND CONTROLLER
 */

// Application State
const state = {
  activeView: 'dashboard',
  isRunning: false,
  materias: {},
  config: {},
  logs: [],
  logFilter: 'all',
  newSubjectTags: [],
  soundEnabled: true,
  timerInterval: null,
  startTime: null
};

// Dynamic Safe DOM Elements Proxy
const elements = new Proxy({}, {
  get(target, prop) {
    const mapping = {
      navItems: () => document.querySelectorAll('.nav-item'),
      viewPanels: () => document.querySelectorAll('.view-panel'),
      viewTitle: () => document.getElementById('view-title'),
      viewSubtitle: () => document.getElementById('view-subtitle'),
      
      btnToggleBot: () => document.getElementById('btn-toggle-bot'),
      btnBotIcon: () => document.getElementById('btn-bot-icon'),
      btnBotText: () => document.getElementById('btn-bot-text'),
      heroStateLabel: () => document.getElementById('hero-state-label'),
      globalStatusPill: () => document.getElementById('global-status-pill'),
      globalStatusText: () => document.getElementById('global-status-text'),
      quickStatusDot: () => document.getElementById('quick-status-dot'),
      quickStatusText: () => document.getElementById('quick-status-text'),
      
      metricIntentos: () => document.getElementById('metric-intentos'),
      metricTiempo: () => document.getElementById('metric-tiempo'),
      metricPendientes: () => document.getElementById('metric-pendientes'),
      metricInscritas: () => document.getElementById('metric-inscritas'),
      badgeMaterias: () => document.getElementById('badge-materias'),

      terminalLogs: () => document.getElementById('terminal-logs'),
      logFilter: () => document.getElementById('log-filter'),
      btnClearLogs: () => document.getElementById('btn-clear-logs'),

      materiasContainer: () => document.getElementById('materias-container'),
      searchMaterias: () => document.getElementById('search-materias'),
      btnOpenAddModal: () => document.getElementById('btn-open-add-modal'),
      modalAddMateria: () => document.getElementById('modal-add-materia'),
      btnCloseModal: () => document.getElementById('btn-close-modal'),
      btnCancelModal: () => document.getElementById('btn-cancel-modal'),
      formAddMateria: () => document.getElementById('form-add-materia'),
      modalNombreMateria: () => document.getElementById('modal-nombre-materia'),
      modalSeccionesInput: () => document.getElementById('modal-secciones-input'),
      tagsContainer: () => document.getElementById('tags-container'),
      modalEditOldNombre: () => document.getElementById('modal-edit-old-nombre'),
      modalTitleText: () => document.getElementById('modal-title-text'),
      modalIconElem: () => document.getElementById('modal-icon-elem'),
      modalBtnSubmitText: () => document.getElementById('modal-btn-submit-text'),

      configForm: () => document.getElementById('config-form'),
      cfgUser: () => document.getElementById('cfg-user'),
      cfgPass: () => document.getElementById('cfg-pass'),
      cfgToken: () => document.getElementById('cfg-token'),
      cfgChatid: () => document.getElementById('cfg-chatid'),
      cfgUrlLogin: () => document.getElementById('cfg-urllogin'),
      cfgUrlInsc: () => document.getElementById('cfg-urlinsc'),
      cfgHeadless: () => document.getElementById('cfg-headless'),
      cfgSound: () => document.getElementById('cfg-sound'),
      btnTestSound: () => document.getElementById('btn-test-sound'),
      cfgDriver: () => document.getElementById('cfg-driver'),
      btnTogglePass: () => document.getElementById('btn-toggle-pass'),
      iconEye: () => document.getElementById('icon-eye'),
      btnTestTelegram: () => document.getElementById('btn-test-telegram'),
      
      activationOverlay: () => document.getElementById('activation-overlay'),
      formActivation: () => document.getElementById('form-activation'),
      inputLicenseKey: () => document.getElementById('input-license-key'),
      displayHwid: () => document.getElementById('display-hwid'),
      activationErrorMsg: () => document.getElementById('activation-error-msg'),
      btnActivateLicense: () => document.getElementById('btn-activate-license'),
      btnActivateIcon: () => document.getElementById('btn-activate-icon'),
      btnActivateText: () => document.getElementById('btn-activate-text'),

      toastContainer: () => document.getElementById('toast-container')
    };

    if (mapping[prop]) {
      return mapping[prop]();
    }
    return undefined;
  }
});

// ==========================================================================
// AUDIO ALERTS SYNTHESIZER (Web Audio API)
// ==========================================================================
function playAlertSound(type = 'cupo') {
  if (!state.soundEnabled) return;
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const now = ctx.currentTime;

    if (type === 'cupo' || type === 'success') {
      // Sonido de campana armónica ascendente (C5 -> E5 -> G5 -> C6)
      const notes = [523.25, 659.25, 783.99, 1046.50];
      notes.forEach((freq, i) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now + i * 0.1);
        gain.gain.setValueAtTime(0.25, now + i * 0.1);
        gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.1 + 0.35);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now + i * 0.1);
        osc.stop(now + i * 0.1 + 0.35);
      });
    } else if (type === 'semestre') {
      // Alerta urgente de alta frecuencia
      const freqs = [880, 1174.66, 880, 1174.66];
      freqs.forEach((freq, i) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, now + i * 0.12);
        gain.gain.setValueAtTime(0.3, now + i * 0.12);
        gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.12 + 0.25);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now + i * 0.12);
        osc.stop(now + i * 0.12 + 0.25);
      });
    } else if (type === 'alarm' || type === 'login_failed') {
      // Alarma acústica de emergencia (bip de advertencia estridente)
      const freqs = [920, 460, 920, 460, 920, 460];
      freqs.forEach((freq, i) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(freq, now + i * 0.14);
        gain.gain.setValueAtTime(0.32, now + i * 0.14);
        gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.14 + 0.12);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now + i * 0.14);
        osc.stop(now + i * 0.14 + 0.12);
      });
    }
  } catch (e) {
    console.warn("Audio Context error:", e);
  }
}

// ==========================================================================
// CRONÓMETRO DE TIEMPO ACTIVO
// ==========================================================================
function startActiveTimer() {
  if (state.timerInterval) clearInterval(state.timerInterval);
  if (!state.startTime) state.startTime = Date.now();

  state.timerInterval = setInterval(() => {
    if (!state.isRunning) return;
    const elapsedSeconds = Math.floor((Date.now() - state.startTime) / 1000);
    const hrs = String(Math.floor(elapsedSeconds / 3600)).padStart(2, '0');
    const mins = String(Math.floor((elapsedSeconds % 3600) / 60)).padStart(2, '0');
    const secs = String(elapsedSeconds % 60).padStart(2, '0');
    if (elements.metricTiempo) {
      elements.metricTiempo.textContent = `${hrs}:${mins}:${secs}`;
    }
  }, 1000);
}

function stopActiveTimer() {
  if (state.timerInterval) {
    clearInterval(state.timerInterval);
    state.timerInterval = null;
  }
}

// ==========================================================================
// TOAST NOTIFICATIONS
// ==========================================================================
function showToast(message, type = 'info', duration = 3500) {
  const icons = {
    success: 'check-circle',
    error: 'alert-triangle',
    warning: 'alert-circle',
    info: 'info'
  };

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <div class="toast-icon"><i data-lucide="${icons[type] || 'info'}"></i></div>
    <div class="toast-content">${message}</div>
  `;

  elements.toastContainer.appendChild(toast);
  lucide.createIcons({ root: toast });

  setTimeout(() => {
    toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ==========================================================================
// NAVIGATION & VIEW SWITCHING
// ==========================================================================
function initNavigation() {
  const titles = {
    dashboard: { title: 'Dashboard', sub: 'Monitoreo en tiempo real y centro de control' },
    materias: { title: 'Gestión de Materias', sub: 'Administra tus asignaturas y el orden de prioridad de las secciones' },
    config: { title: 'Configuración', sub: 'Credenciales, enlaces de Terna y notificaciones' }
  };

  elements.navItems.forEach(item => {
    item.addEventListener('click', () => {
      const view = item.dataset.view;
      if (!view) return;

      elements.navItems.forEach(n => n.classList.remove('active'));
      item.classList.add('active');

      elements.viewPanels.forEach(p => p.classList.remove('active'));
      const targetPanel = document.getElementById(`view-${view}`);
      if (targetPanel) targetPanel.classList.add('active');

      if (titles[view]) {
        elements.viewTitle.textContent = titles[view].title;
        elements.viewSubtitle.textContent = titles[view].sub;
      }
      state.activeView = view;
    });
  });
}

// ==========================================================================
// PYWEBVIEW BRIDGE & REALTIME EVENTS
// ==========================================================================
window.onBridgeEvent = function(event) {
  if (!event || !event.type) return;

  switch (event.type) {
    case 'log':
      appendLog(event.data);
      break;
    case 'bot_status':
      updateBotStatusUI(event.data);
      break;
    case 'stats_updated':
      if (event.data) {
        if (event.data.intentos !== undefined && elements.metricIntentos) {
          elements.metricIntentos.textContent = event.data.intentos;
          elements.metricIntentos.classList.remove('pulse-anim');
          void elements.metricIntentos.offsetWidth;
          elements.metricIntentos.classList.add('pulse-anim');

          if (state.isRunning && event.data.intentos > 0 && elements.globalStatusText) {
            elements.globalStatusText.textContent = `Intento ${event.data.intentos} | Monitoreando cupos...`;
          }
        }
        if (event.data.materias_pendientes !== undefined && elements.metricPendientes) {
          elements.metricPendientes.textContent = event.data.materias_pendientes;
        }
        if (event.data.materias_inscritas !== undefined && elements.metricInscritas) {
          elements.metricInscritas.textContent = event.data.materias_inscritas;
        }
      }
      break;
    case 'login_failed':
      playAlertSound('alarm');
      showToast(event.data?.message || '🚨 ALERTA: No se pudo iniciar sesión en Terna. Revisa tus credenciales.', 'error', 6000);
      if (elements.globalStatusPill) {
        elements.globalStatusPill.className = 'header-status-pill error';
      }
      if (elements.globalStatusText) {
        elements.globalStatusText.textContent = '🚨 Error de Sesión en Terna';
      }
      if (elements.heroStateLabel) {
        elements.heroStateLabel.textContent = 'Error de Autenticación';
      }
      break;
    case 'license_activated':
      if (elements.activationOverlay) {
        elements.activationOverlay.classList.remove('active');
      }
      playAlertSound('success');
      showToast(event.data?.message || '¡Licencia activada con éxito!', 'success');
      break;
    case 'license_revoked':
      if (elements.activationOverlay) {
        elements.activationOverlay.classList.add('active');
      }
      if (elements.activationErrorMsg) {
        elements.activationErrorMsg.textContent = event.data?.message || 'Esta licencia fue revocada o invalidada por el administrador.';
        elements.activationErrorMsg.classList.remove('hidden');
      }
      playAlertSound('alarm');
      showToast(event.data?.message || 'Licencia revocada por el administrador.', 'error', 7000);
      break;
    case 'materias_updated':
      state.materias = event.data;
      renderMaterias();
      updateMetrics();
      break;
  }
};

function isPyWebViewApiReady() {
  return typeof window.pywebview?.api?.get_config === 'function' &&
         typeof window.pywebview?.api?.get_materias === 'function';
}

async function checkLicenseStatus() {
  if (isPyWebViewApiReady()) {
    try {
      if (window.pywebview.api.get_hardware_id) {
        const hwidData = await window.pywebview.api.get_hardware_id();
        if (hwidData && hwidData.hwid && elements.displayHwid) {
          elements.displayHwid.textContent = hwidData.hwid;
        }
      }

      if (window.pywebview.api.get_license_status) {
        const status = await window.pywebview.api.get_license_status();
        if (status && status.active) {
          if (elements.activationOverlay) {
            elements.activationOverlay.classList.remove('active');
          }
          return true;
        } else {
          if (elements.activationOverlay) {
            elements.activationOverlay.classList.add('active');
          }
          if (status && status.message && status.key && elements.activationErrorMsg) {
            elements.activationErrorMsg.textContent = status.message;
            elements.activationErrorMsg.classList.remove('hidden');
          }
          return false;
        }
      }
    } catch (e) {
      console.error("Error verificando licencia:", e);
    }
  }
  return true;
}

async function initAppData() {
  if (isPyWebViewApiReady()) {
    try {
      await checkLicenseStatus();
      await loadConfig();
      await loadMaterias();
      await loadStatus();
    } catch (e) {
      console.error("Error cargando datos iniciales:", e);
    }
  }
}

async function loadStatus() {
  if (isPyWebViewApiReady()) {
    try {
      const st = await window.pywebview.api.get_status();
      if (st) {
        updateBotStatusUI(st);
        if (st.logs && st.logs.length > 0) {
          state.logs = st.logs;
          refreshLogsView();
        }
      }
    } catch (e) {
      console.error("Error loading status:", e);
    }
  }
}

function waitForPyWebView() {
  return new Promise((resolve) => {
    if (isPyWebViewApiReady()) {
      initAppData();
      return resolve();
    }

    // Escuchar el evento oficial que se dispara cuando _createApi ha terminado
    window.addEventListener('pywebviewready', async () => {
      if (isPyWebViewApiReady()) {
        await initAppData();
        resolve();
      }
    });

    // Polling continuo hasta que la función get_config realmente exista en el objeto api
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      if (isPyWebViewApiReady()) {
        clearInterval(interval);
        await initAppData();
        resolve();
      }
      if (attempts > 160) { // 8 segundos máximo
        clearInterval(interval);
        resolve();
      }
    }, 50);
  });
}

// ==========================================================================
// LOGS & TERMINAL MANAGEMENT
// ==========================================================================
function appendLog(logEntry) {
  state.logs.push(logEntry);
  if (state.logs.length > 300) state.logs.shift();

  // Disparar alertas sonoras inteligentes
  if (logEntry.level === 'login_failed') {
    playAlertSound('alarm');
  } else if (logEntry.level === 'success' || (logEntry.message && logEntry.message.toLowerCase().includes('cupo detectado'))) {
    playAlertSound('cupo');
  } else if (logEntry.level === 'warning' && logEntry.message && logEntry.message.toLowerCase().includes('nuevo semestre')) {
    playAlertSound('semestre');
  }

  // If filtered out, do not display
  if (state.logFilter !== 'all' && logEntry.level !== state.logFilter) {
    return;
  }

  const line = document.createElement('div');
  line.className = `log-line ${logEntry.level || 'info'}`;
  line.innerHTML = `
    <span class="log-time">[${logEntry.timestamp || '00:00:00'}]</span>
    <span class="log-badge ${logEntry.level || 'info'}">${(logEntry.level || 'INFO').toUpperCase()}</span>
    <span class="log-msg">${escapeHtml(logEntry.message || '')}</span>
  `;

  elements.terminalLogs.appendChild(line);
  elements.terminalLogs.scrollTop = elements.terminalLogs.scrollHeight;
}

function refreshLogsView() {
  elements.terminalLogs.innerHTML = '';
  const filtered = state.logFilter === 'all' 
    ? state.logs 
    : state.logs.filter(l => l.level === state.logFilter);

  filtered.forEach(logEntry => {
    const line = document.createElement('div');
    line.className = `log-line ${logEntry.level || 'info'}`;
    line.innerHTML = `
      <span class="log-time">[${logEntry.timestamp || '00:00:00'}]</span>
      <span class="log-badge ${logEntry.level || 'info'}">${(logEntry.level || 'INFO').toUpperCase()}</span>
      <span class="log-msg">${escapeHtml(logEntry.message || '')}</span>
    `;
    elements.terminalLogs.appendChild(line);
  });
  elements.terminalLogs.scrollTop = elements.terminalLogs.scrollHeight;
}

function escapeHtml(text) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return String(text).replace(/[&<>"']/g, m => map[m]);
}

// ==========================================================================
// BOT STATUS UI UPDATE
// ==========================================================================
function updateBotStatusUI(statusData) {
  state.isRunning = statusData.running;

  if (state.isRunning) {
    elements.btnToggleBot.className = 'btn-hero-action stop';
    elements.btnBotText.textContent = 'Detener Bot';
    elements.btnBotIcon.setAttribute('data-lucide', 'square');
    
    elements.heroStateLabel.textContent = 'Bot en Ejecución';
    elements.globalStatusPill.className = 'header-status-pill running';
    elements.globalStatusText.textContent = 'Monitoreando Cupos...';
    
    elements.quickStatusDot.className = 'status-indicator-dot active';
    elements.quickStatusText.textContent = 'Ejecutando';

    startActiveTimer();
  } else {
    elements.btnToggleBot.className = 'btn-hero-action start';
    elements.btnBotText.textContent = 'Iniciar Inscripción';
    elements.btnBotIcon.setAttribute('data-lucide', 'play');

    elements.heroStateLabel.textContent = 'Bot en Espera';
    elements.globalStatusPill.className = 'header-status-pill';
    elements.globalStatusText.textContent = 'Listo para iniciar';

    elements.quickStatusDot.className = 'status-indicator-dot';
    elements.quickStatusText.textContent = 'Inactivo';

    stopActiveTimer();
  }

  if (statusData.stats) {
    if (statusData.stats.intentos !== undefined) {
      elements.metricIntentos.textContent = statusData.stats.intentos;
    }
  }

  updateMetrics();
  lucide.createIcons({ root: elements.btnToggleBot });
}

function updateMetrics() {
  let pendientes = 0;
  let inscritas = 0;

  Object.values(state.materias).forEach(m => {
    if (m.inscrita) inscritas++;
    else pendientes++;
  });

  elements.metricPendientes.textContent = pendientes;
  elements.metricInscritas.textContent = inscritas;
  elements.badgeMaterias.textContent = Object.keys(state.materias).length;
}

// ==========================================================================
// MATERIAS MANAGEMENT
// ==========================================================================
function renderMaterias() {
  elements.materiasContainer.innerHTML = '';
  const search = elements.searchMaterias.value.trim().toUpperCase();
  const keys = Object.keys(state.materias);

  const filteredKeys = keys.filter(k => k.includes(search));

  if (filteredKeys.length === 0) {
    elements.materiasContainer.innerHTML = `
      <div class="empty-state">
        <i data-lucide="book-x"></i>
        <h3>No se encontraron materias</h3>
        <p>Haz clic en "Agregar Materia" para registrar una asignatura.</p>
      </div>
    `;
    lucide.createIcons({ root: elements.materiasContainer });
    return;
  }

  filteredKeys.forEach(nombre => {
    const info = state.materias[nombre];
    const card = document.createElement('div');
    card.className = `materia-card glass-panel ${info.inscrita ? 'inscrita' : ''}`;

    const numSecs = (info.secciones || []).length;
    const seccionesHtml = (info.secciones || []).map((sec, idx) => `
      <span class="seccion-pill" title="Prioridad ${idx + 1}">
        ${idx > 0 ? `<button class="priority-arrow-btn move-left" data-nombre="${escapeHtml(nombre)}" data-idx="${idx}" title="Subir prioridad (mover a la izquierda)">&#9664;</button>` : ''}
        <span class="priority-num">#${idx + 1}</span>
        <span>${escapeHtml(sec)}</span>
        ${idx < numSecs - 1 ? `<button class="priority-arrow-btn move-right" data-nombre="${escapeHtml(nombre)}" data-idx="${idx}" title="Bajar prioridad (mover a la derecha)">&#9654;</button>` : ''}
      </span>
    `).join('');

    card.innerHTML = `
      <div class="materia-card-header">
        <h4 class="materia-title">${escapeHtml(nombre)}</h4>
        <span class="materia-badge ${info.inscrita ? 'inscrita' : 'pendiente'}">
          ${info.inscrita ? 'Inscrita' : 'Pendiente'}
        </span>
      </div>

      <div class="secciones-container">
        <span class="secciones-label">Secciones (por prioridad):</span>
        <div class="secciones-list">${seccionesHtml}</div>
      </div>

      <div class="materia-card-footer">
        <label class="status-toggle-wrap">
          <input type="checkbox" class="toggle-inscrita-chk" data-nombre="${escapeHtml(nombre)}" ${info.inscrita ? 'checked' : ''}>
          <span>${info.inscrita ? 'Marcada como lista' : 'Pendiente de inscribir'}</span>
        </label>
        <div class="materia-actions">
          <button class="btn-edit-materia" data-nombre="${escapeHtml(nombre)}" title="Editar Materia y Secciones">
            <i data-lucide="edit-3"></i>
          </button>
          <button class="btn-delete-materia" data-nombre="${escapeHtml(nombre)}" title="Eliminar Materia">
            <i data-lucide="trash-2"></i>
          </button>
        </div>
      </div>
    `;

    // Event handlers for priority arrows
    card.querySelectorAll('.priority-arrow-btn.move-left').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const idx = parseInt(btn.dataset.idx, 10);
        const secciones = [...(info.secciones || [])];
        if (idx > 0) {
          const temp = secciones[idx];
          secciones[idx] = secciones[idx - 1];
          secciones[idx - 1] = temp;
          if (window.pywebview && window.pywebview.api) {
            await window.pywebview.api.update_secciones(nombre, secciones);
            showToast(`Sección ${temp} subió a Prioridad #${idx}`, 'info');
          }
        }
      });
    });

    card.querySelectorAll('.priority-arrow-btn.move-right').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const idx = parseInt(btn.dataset.idx, 10);
        const secciones = [...(info.secciones || [])];
        if (idx < secciones.length - 1) {
          const temp = secciones[idx];
          secciones[idx] = secciones[idx + 1];
          secciones[idx + 1] = temp;
          if (window.pywebview && window.pywebview.api) {
            await window.pywebview.api.update_secciones(nombre, secciones);
            showToast(`Sección ${temp} bajó a Prioridad #${idx + 2}`, 'info');
          }
        }
      });
    });

    // Event handlers for toggle, edit and delete
    const toggleChk = card.querySelector('.toggle-inscrita-chk');
    toggleChk.addEventListener('change', async (e) => {
      const isChecked = e.target.checked;
      if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.toggle_materia_inscrita(nombre, isChecked);
        showToast(`Materia "${nombre}" actualizada.`, 'info');
      }
    });

    const editBtn = card.querySelector('.btn-edit-materia');
    editBtn.addEventListener('click', () => {
      openEditModal(nombre);
    });

    const deleteBtn = card.querySelector('.btn-delete-materia');
    deleteBtn.addEventListener('click', async () => {
      if (confirm(`¿Seguro que deseas eliminar la materia "${nombre}"?`)) {
        if (window.pywebview && window.pywebview.api) {
          await window.pywebview.api.delete_materia(nombre);
          showToast(`Materia "${nombre}" eliminada.`, 'warning');
        }
      }
    });

    elements.materiasContainer.appendChild(card);
  });

  lucide.createIcons({ root: elements.materiasContainer });
}

function openAddModal() {
  state.newSubjectTags = [];
  renderTags();
  elements.modalEditOldNombre.value = '';
  elements.modalNombreMateria.value = '';
  elements.modalSeccionesInput.value = '';
  elements.modalTitleText.textContent = 'Agregar Materia';
  elements.modalBtnSubmitText.textContent = 'Guardar Materia';
  elements.modalIconElem.setAttribute('data-lucide', 'book-plus');
  lucide.createIcons({ root: elements.modalAddMateria });
  elements.modalAddMateria.classList.add('active');
  elements.modalNombreMateria.focus();
}

function openEditModal(nombre) {
  const info = state.materias[nombre] || {};
  state.newSubjectTags = [...(info.secciones || [])];
  renderTags();
  elements.modalEditOldNombre.value = nombre;
  elements.modalNombreMateria.value = nombre;
  elements.modalSeccionesInput.value = '';
  elements.modalTitleText.textContent = 'Editar Materia';
  elements.modalBtnSubmitText.textContent = 'Guardar Cambios';
  elements.modalIconElem.setAttribute('data-lucide', 'edit-3');
  lucide.createIcons({ root: elements.modalAddMateria });
  elements.modalAddMateria.classList.add('active');
  elements.modalNombreMateria.focus();
}

// ==========================================================================
// TAGS INPUT (MODAL AGREGAR / EDITAR MATERIA)
// ==========================================================================
function renderTags() {
  // Remove existing badges
  const existingBadges = elements.tagsContainer.querySelectorAll('.tag-badge');
  existingBadges.forEach(b => b.remove());

  state.newSubjectTags.forEach((tag, idx) => {
    const badge = document.createElement('span');
    badge.className = 'tag-badge';
    badge.innerHTML = `
      <span>#${idx + 1} ${escapeHtml(tag)}</span>
      <span class="remove-tag" data-idx="${idx}">&times;</span>
    `;
    elements.tagsContainer.insertBefore(badge, elements.modalSeccionesInput);
  });

  const removeBtns = elements.tagsContainer.querySelectorAll('.remove-tag');
  removeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = parseInt(btn.dataset.idx, 10);
      state.newSubjectTags.splice(idx, 1);
      renderTags();
    });
  });
}

function initTagsInput() {
  if (elements.modalSeccionesInput) {
    elements.modalSeccionesInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ',') {
        e.preventDefault();
        const val = elements.modalSeccionesInput.value.trim().toUpperCase();
        if (val && !state.newSubjectTags.includes(val)) {
          state.newSubjectTags.push(val);
          elements.modalSeccionesInput.value = '';
          renderTags();
        }
      } else if (e.key === 'Backspace' && elements.modalSeccionesInput.value === '') {
        if (state.newSubjectTags.length > 0) {
          state.newSubjectTags.pop();
          renderTags();
        }
      }
    });
  }
}

// ==========================================================================
// CONFIG FORM
// ==========================================================================
async function loadConfig() {
  if (isPyWebViewApiReady()) {
    try {
      const cfg = await window.pywebview.api.get_config();
      state.config = cfg || {};

      if (elements.cfgUser) elements.cfgUser.value = cfg.USER_UNI || '';
      if (elements.cfgPass) elements.cfgPass.value = cfg.PASS_UNI || '';
      if (elements.cfgToken) elements.cfgToken.value = cfg.TOKEN || '';
      if (elements.cfgChatid) elements.cfgChatid.value = cfg.CHAT_ID || '';
      if (elements.cfgUrlLogin) elements.cfgUrlLogin.value = cfg.URL_LOGIN || 'https://usm.terna.net/';
      if (elements.cfgUrlInsc) elements.cfgUrlInsc.value = cfg.URL_INSCRIPCION || 'https://usm.terna.net/Inscripcion.php?mid=0';
      if (elements.cfgHeadless) elements.cfgHeadless.checked = !!cfg.HEADLESS;
      if (elements.cfgDriver) elements.cfgDriver.value = cfg.CHROMEDRIVER_PATH || '';
    } catch (e) {
      console.error("Error cargando configuración:", e);
    }
  }
}

async function loadMaterias() {
  if (isPyWebViewApiReady()) {
    try {
      const res = await window.pywebview.api.get_materias();
      if (res && res.success) {
        state.materias = res.materias || {};
        renderMaterias();
        updateMetrics();
      }
    } catch (e) {
      console.error("Error cargando materias:", e);
    }
  }
}

// ==========================================================================
// INITIALIZATION & EVENT LISTENERS
// ==========================================================================
document.addEventListener('DOMContentLoaded', async () => {
  lucide.createIcons();
  initNavigation();
  initTagsInput();

  await waitForPyWebView();
  await loadConfig();
  await loadMaterias();

  // Toggle Bot Button
  if (elements.btnToggleBot) {
    elements.btnToggleBot.addEventListener('click', async () => {
      if (!window.pywebview || !window.pywebview.api) {
        showToast('Error: Bridge con Python no disponible', 'error');
        return;
      }

      if (state.isRunning) {
        const res = await window.pywebview.api.stop_bot();
        if (res && res.success) showToast(res.message, 'warning');
      } else {
        const res = await window.pywebview.api.start_bot();
        if (res && res.success) {
          showToast(res.message, 'success');
        } else {
          showToast(res ? res.message : 'Error al iniciar bot', 'error');
        }
      }
    });
  }

  // Log filter
  if (elements.logFilter) {
    elements.logFilter.addEventListener('change', (e) => {
      state.logFilter = e.target.value;
      refreshLogsView();
    });
  }

  // Clear logs
  if (elements.btnClearLogs) {
    elements.btnClearLogs.addEventListener('click', () => {
      state.logs = [];
      if (elements.terminalLogs) elements.terminalLogs.innerHTML = '';
      showToast('Consola limpiada.', 'info');
    });
  }

  // Search materias
  if (elements.searchMaterias) {
    elements.searchMaterias.addEventListener('input', () => {
      renderMaterias();
    });
  }

  // Modal open/close
  if (elements.btnOpenAddModal) {
    elements.btnOpenAddModal.addEventListener('click', openAddModal);
  }

  const closeModal = () => {
    if (elements.modalAddMateria) elements.modalAddMateria.classList.remove('active');
  };
  if (elements.btnCloseModal) elements.btnCloseModal.addEventListener('click', closeModal);
  if (elements.btnCancelModal) elements.btnCancelModal.addEventListener('click', closeModal);

  // Form Add / Edit Materia
  if (elements.formAddMateria) {
    elements.formAddMateria.addEventListener('submit', async (e) => {
      e.preventDefault();
      const nombre = elements.modalNombreMateria ? elements.modalNombreMateria.value.trim().toUpperCase() : '';
      
      const pendingTag = elements.modalSeccionesInput ? elements.modalSeccionesInput.value.trim().toUpperCase() : '';
      if (pendingTag && !state.newSubjectTags.includes(pendingTag)) {
        state.newSubjectTags.push(pendingTag);
      }

      if (!nombre) {
        showToast('Ingresa el nombre de la materia', 'warning');
        return;
      }

      if (state.newSubjectTags.length === 0) {
        showToast('Agrega al menos una sección (ej. 1MB)', 'warning');
        return;
      }

      const oldNombre = elements.modalEditOldNombre ? elements.modalEditOldNombre.value : '';
      const isEditing = !!oldNombre;

      if (window.pywebview && window.pywebview.api) {
        let res;
        if (isEditing) {
          res = await window.pywebview.api.edit_materia(oldNombre, nombre, state.newSubjectTags);
        } else {
          res = await window.pywebview.api.add_materia(nombre, state.newSubjectTags);
        }

        if (res && res.success) {
          showToast(isEditing ? `Materia "${nombre}" actualizada exitosamente.` : `Materia "${nombre}" agregada correctamente.`, 'success');
          closeModal();
        } else {
          showToast(res ? res.message : 'Error al procesar materia.', 'error');
        }
      }
    });
  }

  // Password visibility toggle
  if (elements.btnTogglePass && elements.cfgPass) {
    elements.btnTogglePass.addEventListener('click', () => {
      const isPass = elements.cfgPass.type === 'password';
      elements.cfgPass.type = isPass ? 'text' : 'password';
      if (elements.iconEye) {
        elements.iconEye.setAttribute('data-lucide', isPass ? 'eye-off' : 'eye');
        lucide.createIcons({ root: elements.btnTogglePass });
      }
    });
  }

  // Sound alert test and toggle
  if (elements.btnTestSound) {
    elements.btnTestSound.addEventListener('click', () => {
      playAlertSound('cupo');
      showToast('🎵 Reproduciendo sonido de prueba (Campana de cupo detectado)', 'info');
    });
  }

  if (elements.cfgSound) {
    elements.cfgSound.addEventListener('change', (e) => {
      state.soundEnabled = e.target.checked;
      showToast(state.soundEnabled ? 'Alertas sonoras activadas.' : 'Alertas sonoras desactivadas.', 'info');
    });
  }

  // Test Telegram button
  if (elements.btnTestTelegram) {
    elements.btnTestTelegram.addEventListener('click', async () => {
      const token = elements.cfgToken ? elements.cfgToken.value.trim() : '';
      const chatId = elements.cfgChatid ? elements.cfgChatid.value.trim() : '';
      
      if (!token || !chatId) {
        showToast('Completa el Token y Chat ID antes de probar.', 'warning');
        return;
      }

      elements.btnTestTelegram.disabled = true;
      showToast('Enviando mensaje de prueba a Telegram...', 'info');

      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.test_telegram(token, chatId);
        elements.btnTestTelegram.disabled = false;
        if (res && res.success) {
          showToast(res.message, 'success');
        } else {
          showToast(res ? res.message : 'Error probando Telegram.', 'error');
        }
      }
    });
  }

  // Save config form
  if (elements.configForm) {
    elements.configForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const configData = {
        USER_UNI: elements.cfgUser ? elements.cfgUser.value.trim() : '',
        PASS_UNI: elements.cfgPass ? elements.cfgPass.value.trim() : '',
        TOKEN: elements.cfgToken ? elements.cfgToken.value.trim() : '',
        CHAT_ID: elements.cfgChatid ? elements.cfgChatid.value.trim() : '',
        URL_LOGIN: elements.cfgUrlLogin ? elements.cfgUrlLogin.value.trim() : '',
        URL_INSCRIPCION: elements.cfgUrlInsc ? elements.cfgUrlInsc.value.trim() : '',
        HEADLESS: elements.cfgHeadless ? elements.cfgHeadless.checked : false,
        CHROMEDRIVER_PATH: elements.cfgDriver ? elements.cfgDriver.value.trim() : ''
      };

      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.save_config(configData);
        if (res && res.success) {
          showToast('¡Configuración guardada exitosamente!', 'success');
        } else {
          showToast('Error al guardar configuración.', 'error');
        }
      }
    });
  }

  // Activation Lock Form
  if (elements.formActivation) {
    // Auto-formatear a mayúsculas
    if (elements.inputLicenseKey) {
      elements.inputLicenseKey.addEventListener('input', (e) => {
        e.target.value = e.target.value.toUpperCase();
      });
    }

    elements.formActivation.addEventListener('submit', async (e) => {
      e.preventDefault();
      const key = (elements.inputLicenseKey.value || '').trim().toUpperCase();
      if (!key) {
        showToast('Ingresa una clave de activación', 'warning');
        return;
      }

      elements.btnActivateLicense.disabled = true;
      elements.btnActivateText.textContent = 'Verificando...';
      if (elements.activationErrorMsg) {
        elements.activationErrorMsg.classList.add('hidden');
      }

      if (window.pywebview && window.pywebview.api && window.pywebview.api.activate_license) {
        try {
          const res = await window.pywebview.api.activate_license(key);
          elements.btnActivateLicense.disabled = false;
          elements.btnActivateText.textContent = 'Activar Licencia';

          if (res.success) {
            playAlertSound('success');
            showToast(res.message || '¡Licencia activada con éxito!', 'success');
            if (elements.activationOverlay) {
              elements.activationOverlay.classList.remove('active');
            }
          } else {
            playAlertSound('alarm');
            if (elements.activationErrorMsg) {
              elements.activationErrorMsg.textContent = res.message || 'Clave no válida o ya utilizada.';
              elements.activationErrorMsg.classList.remove('hidden');
            }
          }
        } catch (err) {
          elements.btnActivateLicense.disabled = false;
          elements.btnActivateText.textContent = 'Activar Licencia';
          if (elements.activationErrorMsg) {
            elements.activationErrorMsg.textContent = 'Error de conexión: ' + err.toString();
            elements.activationErrorMsg.classList.remove('hidden');
          }
        }
      } else {
        elements.btnActivateLicense.disabled = false;
        elements.btnActivateText.textContent = 'Activar Licencia';
        showToast('El puente de activación no está disponible.', 'error');
      }
    });
  }
});
