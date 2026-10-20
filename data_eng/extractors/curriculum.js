() => {
  const textOf = (el) => (el ? el.textContent.trim() : '');
  const toInt = (s) => parseInt(s, 10) || 0;

  const splitCode = (s) => {
    const i = s.indexOf(' - ');
    if (i < 0) return null;
    return { code: s.slice(0, i).trim(), name: s.slice(i + 3).trim() };
  };

  const readDetail = (cell, label, idSuffix) => {
    const rows = Array.from(cell.querySelectorAll('table > tbody > tr'));
    const labelRow = rows.find((tr) => textOf(tr.querySelector('span.edit')) === label);
    const table = labelRow?.nextElementSibling?.querySelector(`table[id$=":${idSuffix}"]`);
    const span = table?.querySelector('span.editPesquisa');
    if (!span) return [];
    return span.innerHTML.split(/<br\s*\/?>/i)
      .map((item) => splitCode(item.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim()))
      .filter(Boolean);
  };

  const mainTable = document.getElementById('formDetalharPerfilCurricular:tabelas');
  if (!mainTable) return { error: 'Curriculum main table not found.' };

  const blocks = [];
  for (const blockRow of mainTable.querySelectorAll('tbody > tr')) {
    const blockName = blockRow.querySelector('span.editBold');
    const coursesTable = blockRow.querySelector('table[id*=":tabelaComponentePerfil"]');
    if (!blockName || !coursesTable) continue;

    const subjects = [];
    for (const row of coursesTable.querySelectorAll('tbody > tr')) {
      const c = row.children;
      if (c.length !== 8) continue;
      const course = splitCode(textOf(c[0].querySelector('span.edit')));
      if (!course) continue;

      const item = {
        ...course,
        type: textOf(c[1]),
        period: textOf(c[2]),
        workload: {
          theory: toInt(textOf(c[3])), practice: toInt(textOf(c[4])),
          extension: toInt(textOf(c[5])), total: toInt(textOf(c[6])),
        },
        credits: toInt(textOf(c[7])),
        prerequisites: [], corequisites: [], equivalences: [], syllabus: null,
      };

      const detailButton = row.querySelector('input.botao[id*="btDetalhar_detalhesComponente"]');
      const detail = detailButton && document.getElementById(
        detailButton.id.replace('btDetalhar_detalhesComponente', 'detalhesComponente'));
      if (detail) {
        item.prerequisites = readDetail(detail, 'Pré-Requisitos:', 'preRequisitos');
        item.corequisites = readDetail(detail, 'Co-Requisitos:', 'coRequisitos');
        item.equivalences = readDetail(detail, 'Equivalências:', 'equivalencias');
        const syllabus = detail.querySelector('textarea[id*=":descricaoEmenta"]');
        item.syllabus = syllabus ? syllabus.value.trim() : null;
      }
      subjects.push(item);
    }
    if (subjects.length) blocks.push({ name: textOf(blockName), subjects });
  }
  return { blocks };
}
