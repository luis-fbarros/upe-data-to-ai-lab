// Parses SIGA's "Histórico Escolar" page (ported from the my_ufape app).
() => {
  const parseValue = (text) => {
    if (!text) return null;
    const t = text.trim();
    if (t === '' || t === '-') return null;
    const n = parseFloat(t.replace(',', '.'));
    return isNaN(n) || !/^-?[\d.,]+$/.test(t) ? t : n;
  };
  const splitCodeAndName = (raw) => {
    const m = raw.trim().match(/^([A-Z0-9]+)\s*-\s*(.*)$/);
    return m ? { code: m[1].trim(), name: m[2].trim() } : { code: null, name: raw.trim() };
  };

  const main = document.querySelector('div#content');
  if (!main) return { error: "Main container '#content' not found." };

  const tables = Array.from(main.querySelectorAll('table'));
  const periods = [];
  for (const marker of tables.filter(t => t.innerText.trim().startsWith('Período:'))) {
    const period = marker.querySelector('.editPesquisa.fonte8pt')?.innerText.trim();
    if (!period) continue;
    const obj = { period, subjects: [], period_average: null, period_coefficient: null, special_status: null };

    let content = marker.nextElementSibling;
    while (content && content.tagName !== 'TABLE') content = content.nextElementSibling;
    if (!content) continue;

    const rows = Array.from(content.querySelectorAll('tr'));
    if (rows.length === 1 && rows[0].cells.length === 1) {
      // Term with a special status (e.g. "Trancamento" = enrollment suspended)
      obj.special_status = rows[0].innerText.trim();
    } else {
      for (const row of rows) {
        const cells = row.cells;
        if (cells.length === 6 && cells[0].querySelector('.editPesquisa.fonte8pt')) {
          const { code, name } = splitCodeAndName(cells[0].innerText);
          obj.subjects.push({
            code, name,
            absences: parseValue(cells[1].innerText),
            workload: parseValue(cells[2].innerText),
            credits: parseValue(cells[3].innerText),
            final_grade: parseValue(cells[4].innerText),
            status: parseValue(cells[5].innerText),
          });
        } else if (row.innerText.includes('Média do Período:')) {
          obj.period_average = parseValue(cells[cells.length - 1].innerText);
        } else if (row.innerText.includes('Coeficiente de Rendimento Escolar no Período:')) {
          obj.period_coefficient = parseValue(cells[cells.length - 1].innerText);
        }
      }
    }
    periods.push(obj);
  }

  let overall_average = null;
  let overall_coefficient = null;
  const summary = tables.find(t => t.innerText.includes('Média Geral:'));
  if (summary) {
    for (const row of summary.querySelectorAll('tr')) {
      if (row.innerText.includes('Média Geral:')) {
        overall_average = parseValue(row.cells[row.cells.length - 1].innerText);
      } else if (row.innerText.includes('Coeficiente de Rendimento Escolar Geral:')) {
        overall_coefficient = parseValue(row.cells[row.cells.length - 1].innerText);
      }
    }
  }
  return { periods, overall_average, overall_coefficient };
}
