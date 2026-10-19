// Parses SIGA's "Informações do Discente (header)" page (ported from the my_ufape app).
() => {
  const fieldMapping = {
    'CPF:': 'cpf',
    'Matrícula:': 'registration',
    'Nome:': 'name',
    'Curso:': 'course',
    'Período de Ingresso:': 'entry_period',
    'Tipo do Ingresso:': 'entry_type',
    'Perfil:': 'profile',
    'Turno:': 'shift',
    'Situação:': 'situation',
    'Período Letivo Corrente:': 'current_period',
  };
  const data = {};
  for (const row of document.querySelectorAll('#tableCabecalho tr')) {
    const labelEl = row.querySelector('font.edit');
    const valueEl = row.querySelector('font.editPesquisa');
    if (!labelEl || !valueEl) continue;
    const key = fieldMapping[labelEl.innerText.trim()];
    if (key) data[key] = valueEl.innerText.trim().replace(/\s+/g, ' ');
  }
  if (Object.keys(data).length === 0) return { error: "Table '#tableCabecalho' is empty or missing." };
  return data;
}
