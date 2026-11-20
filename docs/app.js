// ESCOPO: busca pública e somente leitura sobre docs/catalog.json. Nenhuma escrita, nenhuma API, nenhum termo enviado.
const form = document.querySelector('#search-form');
const queryInput = document.querySelector('#query');
const categoryFilter = document.querySelector('#category-filter');
const cards = document.querySelector('#cards');
const count = document.querySelector('#result-count');
const title = document.querySelector('#results-title');
const empty = document.querySelector('#empty-state');
const rankingNote = document.querySelector('#ranking-note');

let catalog = null;
let query = '';

const normalize = (value) => String(value).normalize('NFD').replace(/[̀-ͯ]/g, '').toLocaleLowerCase('pt-BR').trim();
const byId = (records) => new Map(records.map((record) => [record.id, record]));

function sourceLabel(record) {
  if (record.source_state === 'checked') return `Fonte conferida · ${record.checked_at}`;
  if (record.source_state === 'reported') return 'Link informado · não conferido';
  return 'Fonte ainda não conferida';
}

function priceLabel(value) {
  return ({ free: 'Gratuito', freemium: 'Freemium', paid: 'Pago', unknown: 'Preço não conferido' })[value] || value;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function outLink(href, text, className) {
  const link = el('a', className, text);
  link.href = href;
  link.target = '_blank';
  link.rel = 'noopener noreferrer';
  return link;
}

function makeCard(row) {
  const item = row.software;
  const article = el('article', 'card');
  const top = el('div', 'card-top');
  top.append(el('span', 'category', row.categories.map((entry) => entry.name).join(' · ') || 'Sem área'));
  top.append(el('span', `badge ${item.source_state === 'checked' ? '' : item.source_state}`, sourceLabel(item)));

  const refs = el('p', 'for-label');
  if (row.references.length) {
    refs.append(document.createTextNode('Para quem usa '));
    refs.append(el('strong', '', row.references.map((reference) => reference.name).join(', ')));
  } else {
    refs.textContent = 'Software catalogado';
  }

  const alternative = el('section', 'alternative');
  const head = el('div', 'alternative-head');
  head.append(el('h3', '', item.name), outLink(item.url, 'Site do projeto ↗', 'official-link'));
  const meta = el('div', 'meta');
  for (const text of [priceLabel(item.pricing), `Licença: ${item.license}`, ...item.platforms]) meta.append(el('span', '', text));
  alternative.append(head, el('p', '', item.summary), meta, el('p', 'relation-note', item.evidence_note),
    outLink(item.source_url, `Fonte consultada: ${new URL(item.source_url).hostname}`, 'source-link'));
  article.append(top, refs, alternative);
  for (const relation of row.relations) {
    article.append(el('p', 'relation-note', relation.note));
  }
  return article;
}

function search(searchQuery) {
  const references = byId(catalog.references);
  const categories = byId(catalog.categories);
  const needle = normalize(searchQuery);
  const matchingRefs = needle ? catalog.references.filter((item) => [item.name, ...item.aliases].some((value) => {
    const candidate = normalize(value);
    return candidate.includes(needle) || needle.includes(candidate);
  })) : [];
  const targetCategories = new Set(matchingRefs.flatMap((item) => item.category_ids));
  const rows = [];
  for (const item of catalog.software) {
    const relations = catalog.relations.filter((relation) => relation.software_id === item.id
      && (!matchingRefs.length || matchingRefs.some((ref) => ref.id === relation.reference_id)));
    const direct = needle && [item.name, ...item.aliases].some((value) => normalize(value).includes(needle));
    const categoryMatch = needle && item.category_ids.some((id) => {
      const category = categories.get(id);
      return category && [category.name, ...category.aliases].some((value) => normalize(value).includes(needle));
    });
    if (needle && !matchingRefs.length && !direct && !categoryMatch) continue;
    if (matchingRefs.length && !relations.length) continue;
    if (categoryFilter.value && !item.category_ids.includes(categoryFilter.value)) continue;
    rows.push({
      software: item,
      relations,
      references: relations.map((relation) => references.get(relation.reference_id)).filter(Boolean),
      categories: item.category_ids.map((id) => categories.get(id)).filter(Boolean),
      overlap: item.category_ids.filter((id) => targetCategories.has(id)).length,
      relationRank: Math.min(...relations.map((relation) => ({ same_category: 0, partial: 1, related_category: 2 })[relation.match] ?? 9), 3),
      sourceRank: ({ checked: 0, reported: 1, unverified: 2 })[item.source_state] ?? 9,
    });
  }
  rows.sort((a, b) => b.overlap - a.overlap || a.relationRank - b.relationRank || a.sourceRank - b.sourceRank
    || normalize(a.software.name).localeCompare(normalize(b.software.name), 'pt-BR'));
  return { matched: matchingRefs, rows };
}

function render() {
  if (!catalog) return;
  const { matched, rows } = search(query);
  cards.replaceChildren(...rows.map(makeCard));
  count.textContent = `${rows.length} ${rows.length === 1 ? 'alternativa encontrada' : 'alternativas encontradas'}`;
  title.textContent = matched.length ? `Alternativas para ${matched.map((item) => item.name).join(', ')}`
    : query ? `Resultados para “${query}”` : 'Alguns bons pontos de partida';
  empty.hidden = rows.length > 0;
  empty.textContent = query ? `Ainda não há alternativa catalogada para “${query}”. Você pode sugerir uma pelo link abaixo.`
    : 'Não há alternativas para a área escolhida.';
  rankingNote.hidden = rows.length === 0;
  rankingNote.textContent = 'Ordem: mesma área primeiro, depois fonte conferida e nome. Estar na mesma área não garante os mesmos recursos.';
}

function populate() {
  categoryFilter.replaceChildren(new Option('Todas', ''), ...catalog.categories.map((category) => new Option(category.name, category.id)));
  const root = document.querySelector('#popular');
  root.replaceChildren(el('span', '', 'COMECE POR'));
  for (const reference of catalog.references.slice(0, 6)) {
    const label = reference.aliases[0] ? reference.aliases[0][0].toLocaleUpperCase('pt-BR') + reference.aliases[0].slice(1) : reference.name;
    const button = el('button', '', label);
    button.type = 'button';
    button.addEventListener('click', () => {
      queryInput.value = label;
      query = label;
      render();
      document.querySelector('#catalogo').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
    root.append(button);
  }
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  query = queryInput.value.trim();
  render();
  document.querySelector('#catalogo').scrollIntoView({ behavior: 'smooth', block: 'start' });
});
categoryFilter.addEventListener('change', render);

fetch('./catalog.json').then((response) => {
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}).then((data) => {
  catalog = data;
  populate();
  render();
}).catch((error) => {
  empty.hidden = false;
  empty.textContent = `Não foi possível carregar o catálogo (${error.message}).`;
});
