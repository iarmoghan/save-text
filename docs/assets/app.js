const STORAGE_KEY = 'save-text.pastes';

function readPastes() {
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return [];
  }
  try {
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      return parsed.map((item) => ({
        id: item.id,
        content: item.content ?? '',
        createdAt: item.createdAt ?? item.created_at ?? new Date().toISOString(),
      }));
    }
  } catch (error) {
    console.warn('Unable to parse saved pastes from localStorage', error);
  }
  return [];
}

function writePastes(pastes) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(pastes));
}

export function storageAvailable() {
  try {
    const probeKey = `${STORAGE_KEY}.__probe__`;
    window.localStorage.setItem(probeKey, 'ok');
    window.localStorage.removeItem(probeKey);
    return true;
  } catch (error) {
    console.error('Local storage is not available', error);
    return false;
  }
}

export function listPastes() {
  return readPastes().sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
  );
}

export function createPaste(content) {
  const trimmed = content.trim();
  if (!trimmed) {
    throw new Error('Paste content cannot be empty.');
  }
  const now = new Date().toISOString();
  const id = (window.crypto && window.crypto.randomUUID)
    ? window.crypto.randomUUID()
    : `paste-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const paste = { id, content: trimmed, createdAt: now };
  const pastes = readPastes();
  pastes.push(paste);
  writePastes(pastes);
  return paste;
}

export function getPaste(id) {
  return readPastes().find((paste) => paste.id === id) || null;
}

export function deletePaste(id) {
  const pastes = readPastes();
  const next = pastes.filter((paste) => paste.id !== id);
  if (next.length === pastes.length) {
    return false;
  }
  writePastes(next);
  return true;
}

export function snippetFrom(content) {
  const firstLine = content.split(/\r?\n/)[0];
  if (firstLine.length > 120) {
    return `${firstLine.slice(0, 117)}...`;
  }
  if (firstLine.trim().length === 0) {
    return content.slice(0, 120) + (content.length > 120 ? '...' : '');
  }
  return firstLine;
}

export function formatDate(isoString) {
  try {
    const date = new Date(isoString);
    if (!Number.isNaN(date.getTime())) {
      return date.toLocaleString();
    }
  } catch (error) {
    console.warn('Unable to format date', isoString, error);
  }
  return 'Unknown time';
}
