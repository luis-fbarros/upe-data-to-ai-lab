// Parses SIGA's "Grade de Horário" page (ported from the my_ufape app).
() => {
  const subjects = new Map();
  for (const row of document.querySelectorAll('table[width="600"] tr')) {
    const cells = row.querySelectorAll('td font.editPesquisa');
    if (cells.length < 6) continue; // notice rows ("não há vagas") etc.
    const code = cells[0].innerText.trim();
    if (!code || code === 'CÓDIGO') continue;
    subjects.set(code, {
      code,
      name: cells[1].innerText.trim(),
      class_name: cells[2].innerText.trim(),
      room: cells[4].innerText.trim(),
      status: cells[5].innerText.trim(),
      time_slots: [],
    });
  }

  const days = ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB'];
  for (const row of document.querySelectorAll('table[width="570"] tr')) {
    const cells = row.querySelectorAll('td.textoTabela');
    if (cells.length !== 6) continue;
    cells.forEach((cell, i) => {
      const html = cell.innerHTML;
      if (!/<br\s*\/?>/i.test(html)) return;
      const parts = html.split(/<br\s*\/?>/i);
      const codeMatch = parts[0].match(/([A-Z0-9]+)\s*-\s*([A-Z0-9]+)/);
      const timeMatch = (parts[1] || '').match(/(\d{2}:\d{2})\s*às\s*(\d{2}:\d{2})/);
      if (!codeMatch || !timeMatch) return;
      const subject = subjects.get(codeMatch[1]);
      if (subject) subject.time_slots.push({ day: days[i], start: timeMatch[1], end: timeMatch[2] });
    });
  }
  return { subjects: Array.from(subjects.values()) };
}
