(() => {
  const CLASS_LABELS = {
    'repository/ci': 'Repository / CI',
    'runtime-readonly': 'Runtime · Read-only',
    'runtime-write-smoke': 'Runtime · Write-Smoke',
    'deployment/hardware': 'Deployment / Hardware',
    'operator-waiver/deferred': 'Operator · Waiver / Deferred',
  };
  const STATUS_LABELS = {
    passed: 'bestanden',
    failed: 'fehlgeschlagen',
    pending: 'ausstehend',
    deferred: 'zurückgestellt',
    waived: 'erlassen',
    'not-applicable': 'nicht anwendbar',
  };
  const STATUS_CLASSES = {
    passed: 'good',
    failed: 'danger',
    pending: 'warn',
    deferred: 'info',
    waived: 'warn',
    'not-applicable': 'info',
  };

  function render() {
    const runtime = window.ProjectCompanion?.getRuntime?.();
    const card = document.getElementById('verificationEvidenceCard');
    const host = document.getElementById('verificationEvidenceList');
    if (!card || !host || !runtime) return;

    const evidence = Array.isArray(runtime.state?.verificationEvidence)
      ? runtime.state.verificationEvidence
      : [];
    card.hidden = evidence.length === 0;
    host.replaceChildren();

    evidence.forEach(item => {
      const row = document.createElement('div');
      const heading = document.createElement('strong');
      const detail = document.createElement('span');
      const policy = document.createElement('small');
      const status = document.createElement('span');

      heading.textContent = CLASS_LABELS[item.class] || item.class || 'Evidenz';
      status.className = `badge ${STATUS_CLASSES[item.status] || ''}`.trim();
      status.textContent = STATUS_LABELS[item.status] || item.status || 'unbekannt';
      detail.textContent = item.detail || 'Kein Detail dokumentiert.';
      policy.className = 'muted';
      policy.textContent = `Release-Policy: ${item.releasePolicy || 'nicht gesetzt'}`;

      row.append(heading, status, detail, policy);
      host.appendChild(row);
    });
  }

  window.setInterval(render, 1000);
  window.setTimeout(render, 100);
})();
