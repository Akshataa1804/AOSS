const BASE_URL = "http://localhost:8000";

// ----------------------------
// Helper for JSON response
// ----------------------------
async function handleJSONResponse(res) {
  const text = await res.text();
  try {
    return JSON.parse(text);
  } catch (err) {
    throw new Error("Invalid server response: " + text);
  }
}

// ----------------------------
// Documents
// ----------------------------
export async function listDocuments() {
  const res = await fetch(`${BASE_URL}/documents`);
  return handleJSONResponse(res);
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });
  return handleJSONResponse(res);
}

// ----------------------------
// Rules
// ----------------------------
export async function extractRules(filename) {
  const res = await fetch(`${BASE_URL}/fetch_rules/${filename}`, { method: "POST" });
  return handleJSONResponse(res);
}

export async function fetchRules(filename) {
  const res = await fetch(`${BASE_URL}/rules`);
  const data = await handleJSONResponse(res);
  // Filter for the selected file
  return { rules: data.rules[`${filename.split(".")[0]}.yml`] || { allowed: [], forbidden: [], required: [] } };
}

export async function addRule(filename, type, value) {
  const url = new URL(`${BASE_URL}/rules`);
  url.searchParams.append("filename", filename);
  url.searchParams.append("rule_type", type);
  url.searchParams.append("rule_value", value);

  const res = await fetch(url, { method: "POST" });
  return handleJSONResponse(res);
}

export async function deleteRule(filename, type, value) {
  const url = new URL(`${BASE_URL}/rules`);
  url.searchParams.append("filename", filename);
  url.searchParams.append("rule_type", type);
  url.searchParams.append("rule_value", value);

  const res = await fetch(url, { method: "DELETE" });
  return handleJSONResponse(res);
}

// ----------------------------
// RAG Query
// ----------------------------
export async function runRAGQuery(filename, query) {
  const res = await fetch(`${BASE_URL}/rag`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  return handleJSONResponse(res);
}
