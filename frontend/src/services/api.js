// Centralized API client for VERITAS with automatic failover between relative proxy (/api)
// and direct localhost backend (http://127.0.0.1:8000)

let cachedBaseUrl = null;

async function resolveBaseUrl() {
  if (cachedBaseUrl !== null) return cachedBaseUrl;

  // Try relative endpoint first (standard Vite dev proxy or prod bundle)
  try {
    const res = await fetch('/api/health', { method: 'GET', signal: AbortSignal.timeout(1500) });
    if (res.ok) {
      cachedBaseUrl = '';
      return '';
    }
  } catch {
    // Relative proxy failed, try direct 127.0.0.1:8000
  }

  try {
    const res = await fetch('http://127.0.0.1:8000/api/health', { method: 'GET', signal: AbortSignal.timeout(1500) });
    if (res.ok) {
      cachedBaseUrl = 'http://127.0.0.1:8000';
      return cachedBaseUrl;
    }
  } catch {
    // Fallback default
  }

  cachedBaseUrl = '';
  return '';
}

export async function fetchHealth() {
  const base = await resolveBaseUrl();
  const url = `${base}/api/health`;
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(3000) });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return await res.json();
  } catch (err) {
    // Retry once with direct fallback if we were using relative
    if (base === '') {
      try {
        const fallbackRes = await fetch('http://127.0.0.1:8000/api/health', { signal: AbortSignal.timeout(3000) });
        if (fallbackRes.ok) {
          cachedBaseUrl = 'http://127.0.0.1:8000';
          return await fallbackRes.json();
        }
      } catch {
        // ignore
      }
    }
    throw err;
  }
}

export async function askQuestion(question, datasetId) {
  const base = await resolveBaseUrl();
  const url = `${base}/api/question`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, dataset_id: datasetId })
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server returned HTTP ${res.status}`);
  }

  return await res.json();
}

export async function fetchDatasetProfile(datasetId) {
  const base = await resolveBaseUrl();
  const url = `${base}/api/dataset/${datasetId}`;
  const res = await fetch(url);

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${res.status}`);
  }

  return await res.json();
}

export async function uploadDatasetFile(file, datasetId = null) {
  const base = await resolveBaseUrl();
  let url = `${base}/api/upload`;
  if (datasetId) {
    url += `?dataset_id=${encodeURIComponent(datasetId)}`;
  }

  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(url, {
    method: 'POST',
    body: formData
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload failed with HTTP ${res.status}`);
  }

  return await res.json();
}

