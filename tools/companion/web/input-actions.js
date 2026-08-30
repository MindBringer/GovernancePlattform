(() => {
  let activeReleaseJobId = null;
  let activeActionJobId = null;

  function actionSpec(id) {
    const runtime = window.ProjectCompanion?.getRuntime?.();
    return (runtime?.actions || []).find(action => action.id === id) || null;
  }

  function setButtonsDisabled(value) {
    document.querySelectorAll('[data-action], #refresh, #loadMemory, #firstRunForm button').forEach(item => { item.disabled = value; });
  }

  function showConsole() {
    window.ProjectCompanion?.showView?.('console', 'Konsole');
    return document.getElementById('output');
  }

  function detailPanel() {
    return {
      panel: document.getElementById('consoleDetailPanel'),
      output: document.getElementById('outputDetails'),
    };
  }

  function resetDetailLog() {
    const detail = detailPanel();
    if (detail.panel) detail.panel.hidden = true;
    if (detail.output) detail.output.textContent = '';
  }

  function renderResult(data, output, fallbackCommand = '') {
    if (!output) return;
    const ok = Boolean(data?.ok);
    const exitCode = data?.exitCode ?? (ok ? 0 : 1);
    const summary = String(data?.summary || `${ok ? 'OK' : 'FEHLER'} · Exit ${exitCode}`);
    const command = String(data?.command || fallbackCommand || '');
    const failureBlock = String(data?.failureBlock || '');
    const legacyOutput = String(data?.output || '');
    const detailLog = String(data?.detailLog || legacyOutput);

    const visible = [summary, command, !ok ? failureBlock : ''].filter(Boolean);
    if (!ok && !failureBlock && legacyOutput) visible.push(legacyOutput);
    output.textContent = visible.join('\n\n');

    const detail = detailPanel();
    if (detail.output) detail.output.textContent = detailLog;
    if (detail.panel) detail.panel.hidden = !detailLog;
  }

  function setConsoleActivity(label, level = '', completed = null, total = null) {
    const state = document.getElementById('consoleState');
    const progress = document.getElementById('releaseProgress');
    const progressText = document.getElementById('releaseProgressText');
    if (state) { state.textContent = label; state.className = `badge ${level}`.trim(); }
    if (progress) {
      const visible = Number.isFinite(completed) && Number.isFinite(total) && total > 0;
      progress.hidden = !visible;
      if (visible) { progress.max = total; progress.value = completed; }
    }
    if (progressText) progressText.textContent = Number.isFinite(completed) && Number.isFinite(total) ? `${completed}/${total} Schritte` : '';
  }

  function nextPaint() {
    return new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  }

  async function collectActionInput(action) {
    let value = null;
    if (action.input) {
      const inputSpec = action.input || {};
      const promptText = [inputSpec.label || 'Eingabe', inputSpec.placeholder || ''].filter(Boolean).join('\n');
      value = window.prompt(promptText, '');
      if (value === null) return { cancelled: true };
      if (inputSpec.required && !String(value).trim()) return { cancelled: true };
    }

    let confirmation = null;
    if (action.requiresConfirmation) {
      confirmation = window.prompt('Bestätigungstext eingeben:');
      if (!confirmation) return { cancelled: true };
    }
    return { cancelled: false, value, confirmation };
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  function elapsedSeconds(job) {
    const startedAtMs = Number(job?.startedAt || 0) * 1000;
    if (!startedAtMs) return 0;
    const endMs = job?.finishedAt ? Number(job.finishedAt) * 1000 : Date.now();
    return Math.max(0, Math.round((endMs - startedAtMs) / 1000));
  }

  function renderBackgroundRunning(job, output) {
    if (!output) return;
    resetDetailLog();
    const elapsed = elapsedSeconds(job);
    const progress = job?.progress || {};
    const completed = Number(progress.completed || 0);
    const total = Number(progress.total || 1);
    setConsoleActivity(progress.label || job?.label || 'Background-Action läuft', 'warn', completed, total);
    output.textContent = [
      `${job?.label || job?.actionId || 'Background-Action'} läuft serverseitig …`,
      `Status: RUNNING · Job ${String(job?.id || '').slice(0, 8)} · ${elapsed}s`,
      `Phase: ${progress.label || progress.phase || 'läuft'}`,
      progress.detail ? `Aktuell: ${progress.detail}` : '',
      '',
      'Die Action läuft unabhängig vom Browser-Request weiter. Ein Browser-Refresh nimmt denselben Job wieder auf.',
    ].filter((line, index, lines) => line || lines[index - 1] !== '').join('\n');
  }

  function renderBackgroundFinished(job, output) {
    const result = job?.result || {};
    const progress = job?.progress || {};
    setConsoleActivity(result.ok ? 'Action abgeschlossen' : 'Action fehlgeschlagen', result.ok ? 'good' : 'danger', Number(progress.completed || 0), Number(progress.total || 1));
    renderResult(result, output, job?.actionId || 'Background action');
  }

  async function fetchActionJob() {
    const response = await fetch('/api/action-job', { cache: 'no-store' });
    const data = await response.json();
    if (!response.ok || !data?.ok) throw new Error('Background-Action-Jobstatus ist nicht verfügbar.');
    return data.job || null;
  }

  async function pollActionJob(jobId, output) {
    if (!jobId) return;
    activeActionJobId = jobId;
    try {
      while (activeActionJobId === jobId) {
        const job = await fetchActionJob();
        if (!job || job.id !== jobId) throw new Error('Background-Action-Jobstatus gehört nicht zum gestarteten Job.');
        if (job.status === 'running') {
          renderBackgroundRunning(job, output);
          await sleep(1000);
          continue;
        }
        renderBackgroundFinished(job, output);
        return;
      }
    } finally {
      if (activeActionJobId === jobId) activeActionJobId = null;
    }
  }

  async function runRegisteredAction(action) {
    if (!action) return;
    const runtime = window.ProjectCompanion.getRuntime();
    const collected = await collectActionInput(action);
    if (collected.cancelled) return;

    const output = showConsole();
    resetDetailLog();
    setButtonsDisabled(true);
    setConsoleActivity(action.background ? 'Background-Action startet' : 'Aktion läuft', 'warn');
    if (output) output.textContent = `Starte ${action.label || action.id} …`;

    try {
      const body = { confirmation: collected.confirmation };
      if (action.input) body.input = collected.value;
      const response = await fetch(`/api/action/${encodeURIComponent(action.id)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': runtime.csrf,
        },
        body: JSON.stringify(body),
      });
      const data = await response.json();

      if (action.background) {
        if (!response.ok || !data.ok || !data.jobId) {
          if (response.status === 409 && data?.job?.actionId && data?.job?.id) {
            renderBackgroundRunning(data.job, output);
            await pollActionJob(String(data.job.id), output);
            return;
          }
          throw new Error(data.error || data.output || `Background-Action konnte nicht gestartet werden (${response.status}).`);
        }
        const initial = await fetchActionJob();
        if (initial?.id === data.jobId && initial.status === 'running') renderBackgroundRunning(initial, output);
        await pollActionJob(String(data.jobId), output);
        return;
      }

      renderResult(data, output, action.id);
      setConsoleActivity(data.ok ? 'Abgeschlossen' : 'Fehlgeschlagen', data.ok ? 'good' : 'danger');
    } catch (error) {
      if (output) output.textContent = `FEHLER · Client/Transport\n\n${error}`;
      setConsoleActivity('Fehlgeschlagen', 'danger');
    } finally {
      setButtonsDisabled(false);
    }
  }

  function renderReleaseRunning(job, output) {
    if (!output) return;
    resetDetailLog();
    const elapsed = elapsedSeconds(job);
    const progress = job?.progress || {};
    const completed = Number(progress.completed || 0);
    const total = Number(progress.total || 10);
    setConsoleActivity(progress.label || 'Release läuft', 'warn', completed, total);
    output.textContent = [
      'Release läuft serverseitig …',
      `Status: RUNNING · Job ${String(job.id || '').slice(0, 8)} · ${elapsed}s`,
      `Phase: ${progress.label || progress.phase || 'Release läuft'}`,
      progress.detail ? `Aktuell: ${progress.detail}` : '',
      '',
      'Die Anzeige aktualisiert sich automatisch. Browser-Refresh oder ein kurzzeitiger UI-Abbruch beendet den Release nicht.',
    ].filter((line, index, lines) => line || lines[index - 1] !== '').join('\n');
  }

  function renderReleaseFinished(job, output) {
    const result = job?.result || {};
    if (!output) return;
    const progress = job?.progress || {};
    setConsoleActivity(result.ok ? 'Release abgeschlossen' : 'Release fehlgeschlagen', result.ok ? 'good' : 'danger', Number(progress.completed || 0), Number(progress.total || 10));
    renderResult(result, output, 'Full release');
  }

  async function fetchReleaseJob() {
    const response = await fetch('/api/release-job', { cache: 'no-store' });
    const data = await response.json();
    if (!response.ok || !data?.ok) {
      throw new Error('Release-Jobstatus ist nicht verfügbar.');
    }
    return data.job || null;
  }

  async function pollRelease(jobId, output) {
    if (!jobId) return;
    activeReleaseJobId = jobId;
    try {
      while (activeReleaseJobId === jobId) {
        const job = await fetchReleaseJob();
        if (!job || job.id !== jobId) {
          throw new Error('Release-Jobstatus gehört nicht zum gestarteten Job.');
        }
        if (job.status === 'running') {
          renderReleaseRunning(job, output);
          await sleep(1000);
          continue;
        }
        renderReleaseFinished(job, output);
        return;
      }
    } finally {
      if (activeReleaseJobId === jobId) activeReleaseJobId = null;
    }
  }

  async function runRelease() {
    const runtime = window.ProjectCompanion?.getRuntime?.();
    if (!runtime?.release?.enabled) return;
    const output = showConsole();
    resetDetailLog();
    setConsoleActivity('Release-Freigabe', 'warn', 0, 10);
    if (output) output.textContent = 'Vollständiger Release ausgewählt. Die Konsole ist bereit; als Nächstes wird die ausdrückliche Freigabe abgefragt.';
    await nextPaint();
    const expected = String(runtime.release.confirmation || '');
    const confirmation = window.prompt(`Bestätigung erforderlich.${expected ? `\nExakt eingeben:\n${expected}` : '\nBestätigungstext eingeben:'}`);
    if (!confirmation) {
      if (output) output.textContent = 'Release nicht gestartet: Freigabe wurde abgebrochen.';
      setConsoleActivity('Nicht gestartet', '');
      return;
    }

    setButtonsDisabled(true);
    setConsoleActivity('Release startet', 'warn', 0, 10);
    if (output) output.textContent = 'Starte vollständigen Release als serverseitigen Job …';

    try {
      const response = await fetch('/api/action/release', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': runtime.csrf,
        },
        body: JSON.stringify({ confirmation }),
      });
      const data = await response.json();
      if (!response.ok || !data.ok || !data.jobId) {
        if (response.status === 409 && data?.job?.id && !data?.job?.actionId) {
          renderReleaseRunning(data.job, output);
          await pollRelease(String(data.job.id), output);
          return;
        }
        throw new Error(data.error || data.output || `Release-Job konnte nicht gestartet werden (${response.status}).`);
      }
      const initial = await fetchReleaseJob();
      if (initial?.id === data.jobId && initial.status === 'running') renderReleaseRunning(initial, output);
      await pollRelease(String(data.jobId), output);
    } catch (error) {
      if (output) output.textContent = `FEHLER · Release-Transport\n\n${error}`;
      setConsoleActivity('Release fehlgeschlagen', 'danger');
    } finally {
      setButtonsDisabled(false);
    }
  }

  async function resumeActionMonitor() {
    try {
      const job = await fetchActionJob();
      if (!job || job.status !== 'running' || activeActionJobId === job.id) return;
      const output = showConsole();
      renderBackgroundRunning(job, output);
      setButtonsDisabled(true);
      await pollActionJob(String(job.id), output);
    } catch (_error) {
      // Startup monitoring is best-effort; normal Companion initialization must remain available.
    } finally {
      setButtonsDisabled(false);
    }
  }

  async function resumeReleaseMonitor() {
    try {
      const job = await fetchReleaseJob();
      if (!job || job.status !== 'running' || activeReleaseJobId === job.id) return;
      const output = showConsole();
      renderReleaseRunning(job, output);
      setButtonsDisabled(true);
      await pollRelease(String(job.id), output);
    } catch (_error) {
      // Startup monitoring is best-effort; normal Companion initialization must remain available.
    } finally {
      setButtonsDisabled(false);
    }
  }

  window.ProjectCompanion.runAction = id => runRegisteredAction(actionSpec(id));
  window.ProjectCompanion.runRelease = runRelease;
  window.ProjectCompanion.resumeActionMonitor = resumeActionMonitor;
  window.ProjectCompanion.resumeReleaseMonitor = resumeReleaseMonitor;

  document.addEventListener('click', event => {
    const button = event.target.closest?.('[data-action]');
    if (!button) return;

    event.preventDefault();
    event.stopImmediatePropagation();
    if (button.dataset.action === 'release') {
      void runRelease();
      return;
    }

    void runRegisteredAction(actionSpec(button.dataset.action));
  }, true);

  window.setTimeout(() => {
    void resumeActionMonitor();
    void resumeReleaseMonitor();
  }, 500);
})();
