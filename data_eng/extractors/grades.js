() => {
  const main = document.getElementById('form-corpo');
  if (!main) return { error: "Container 'form-corpo' not found." };

  const subjects = [];
  for (const periodDiv of main.children) {
    if (periodDiv.tagName !== 'DIV' || !/^\d{4}\.\d$/.test(periodDiv.id)) continue;
    const term = periodDiv.id;

    for (const headerTable of periodDiv.querySelectorAll('table[id="tagrodape"]')) {
      try {
        const nameEl = headerTable.querySelector('font.editPesquisa');
        let parentTable = headerTable.parentElement;
        while (parentTable && parentTable.tagName !== 'TABLE') parentTable = parentTable.parentElement;
        const details = parentTable ? parentTable.nextElementSibling : null;
        if (!nameEl || !details || details.tagName !== 'DIV') continue;

        const name = nameEl.innerText.trim().replace(/\s+/g, ' ');
        const statusEl = details.querySelector('font.editPesquisa > u');
        const status = statusEl ? statusEl.innerText.trim() : 'Cursando';

        let teacher = '';
        outer: for (const table of details.querySelectorAll('table')) {
          for (const row of table.querySelectorAll('tr')) {
            const cells = row.querySelectorAll('td');
            if (cells.length < 2) continue;
            const label = cells[0].querySelector('font.edit b');
            if (label && label.innerText.includes('Docente')) {
              const t = cells[1].querySelector('font.editPesquisa');
              if (t) { teacher = t.innerText.trim(); break outer; }
            }
          }
        }

        const grades = {};
        const headerCells = details.querySelectorAll('td[bgcolor="#FAEBD7"]');
        if (headerCells.length > 0) {
          const headerRow = headerCells[0].parentElement;
          const valueRow = headerRow.nextElementSibling;
          if (valueRow) {
            const headers = Array.from(headerRow.children).map(c => c.innerText.trim());
            const values = Array.from(valueRow.children).map(c => c.innerText.trim());
            for (let i = 1; i < headers.length; i++) {
              if (headers[i] && values[i] && values[i] !== '-') grades[headers[i]] = values[i];
            }
          }
        }

        subjects.push({ name, term, status, grades, teacher });
      } catch (e) {
      }
    }
  }
  return { subjects };
}
