() => {
  const parseNumber = (text) => {
    if (!text || text.trim() === '-') return null;
    const n = parseFloat(text.trim().replace(/\./g, '').replace(',', '.'));
    return isNaN(n) ? null : n;
  };
  const parsePercentage = (text) => {
    if (!text || text.trim() === '-') return null;
    const n = parseFloat(text.trim().replace('%', '').replace(',', '.'));
    return isNaN(n) ? null : n;
  };
  const clean = (s) => s.replace(/-/g, '').replace(/ /g, ' ').trim();

  const workload_summary = [];
  const btn = document.querySelector('input#bt_a1');
  const workloadTable = btn?.nextElementSibling?.nextElementSibling;
  if (workloadTable && workloadTable.tagName === 'TABLE') {
    for (const row of workloadTable.querySelectorAll('tr[id^="a1."]')) {
      const cells = row.querySelectorAll('td');
      const id = row.getAttribute('id');
      if (cells.length < 2 || cells[0].querySelector('.tituloColuna') || id === 'a1.13') continue;

      const nameEl = cells[0].querySelector('font.edit');
      let name = clean(nameEl ? nameEl.innerText : cells[0].innerText);
      const inner = cells[0].querySelector('input.botao2, input.botao_desativado');
      if (inner) {
        if (inner.nextSibling && inner.nextSibling.nodeType === Node.TEXT_NODE) {
          name = clean(inner.nextSibling.textContent);
        } else if (nameEl && nameEl.childNodes.length > 1) {
          const last = nameEl.childNodes[nameEl.childNodes.length - 1];
          if (last.nodeType === Node.TEXT_NODE) name = clean(last.textContent);
        }
      }
      const parts = id.split('.');
      const at = (i, f) => (cells.length > i ? f(cells[i].innerText) : null);
      workload_summary.push({
        id, parent_id: parts.length > 2 ? parts.slice(0, -1).join('.') : null, name,
        integration: at(1, parseNumber),
        completed_hours: at(2, parseNumber),
        completed_percentage: at(3, parsePercentage),
        waived_hours: at(4, parseNumber),
        waived_percentage: at(5, parsePercentage),
        to_complete_hours: at(6, parseNumber),
        to_complete_percentage: at(7, parsePercentage),
      });
    }
  }

  const component_summary = [];
  const componentTable = document.querySelector('table[id="a2.2.1"]');
  if (componentTable) {
    for (const row of componentTable.querySelectorAll('tr')) {
      const cells = row.querySelectorAll('td');
      if (cells.length < 2 || cells[0].querySelector('.tituloColuna')) continue;
      const description = cells[0].innerText.trim();
      if (!description) continue;
      if (description === 'Total de componentes aproveitados') {
        component_summary.push({ description, hours: null, quantity: parseNumber(cells[1].innerText) });
      } else if (description === 'Utilizados como Equivalência**') {
        component_summary.push({ description, hours: null, quantity: cells.length > 2 ? parseNumber(cells[2].innerText) : null });
      } else {
        component_summary.push({
          description,
          hours: parseNumber(cells[1].innerText),
          quantity: cells.length > 2 ? parseNumber(cells[2].innerText) : null,
        });
      }
    }
  }

  const pending = { subjects: [], total_pending_hours: 0 };
  const pendingTable = document.querySelector('table[id="a3.1"]');
  if (pendingTable) {
    for (const row of pendingTable.querySelectorAll('tr')) {
      const cells = row.querySelectorAll('td');
      if (cells.length === 4 && cells[0].querySelector('font.editPesquisa')) {
        const raw = cells[0].querySelector('font.editPesquisa').innerText.trim();
        const nameWithCode = raw.substring(raw.indexOf('.') + 1).trim();
        const m = nameWithCode.match(/^([A-Z0-9]+)\s*-\s*(.*)$/);
        pending.subjects.push({
          code: m ? m[1] : null,
          name: m ? m[2] : nameWithCode,
          workload: parseNumber(cells[1].innerText),
          period: parseNumber(cells[2].innerText),
          credits: parseNumber(cells[3].innerText),
        });
      } else if (row.innerText.includes('TOTAL PENDENTE')) {
        const last = cells[cells.length - 1];
        const b = last?.querySelector('font.editPesquisa > b') ?? last?.querySelector('b');
        const m = (b?.innerText || '').match(/=\s*(\d+)/);
        if (m) pending.total_pending_hours = parseInt(m[1], 10);
      }
    }
  }

  return { workload_summary, component_summary, pending_components: pending };
}
