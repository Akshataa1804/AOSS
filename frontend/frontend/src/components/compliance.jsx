import { useState, useEffect } from "react";
import { ShieldCheck, UploadCloud, FileText, Zap } from "lucide-react";
import axios from "axios";

const API_BASE = "http://localhost:8000"; // change if backend runs elsewhere

export default function Compliance() {
  const [docs, setDocs] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [rules, setRules] = useState({ allowed: [], forbidden: [], required: [] });
  const [newRule, setNewRule] = useState("");
  const [newType, setNewType] = useState("forbidden");
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  // ===== Load Documents from backend =====
  const fetchDocuments = async () => {
    try {
      const res = await axios.get(`${API_BASE}/documents`);
      setDocs(res.data.documents);
    } catch (err) {
      console.error(err);
    }
  };

  // ===== Fetch rules for selected doc =====
  const fetchRules = async (filename) => {
    if (!filename) return;
    try {
      const res = await axios.get(`${API_BASE}/rules`, { params: { filename } });
      setRules(res.data.rules);
    } catch (err) {
      console.error(err);
      setRules({ allowed: [], forbidden: [], required: [] });
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    if (selectedDoc) fetchRules(selectedDoc);
  }, [selectedDoc]);

  // ===== Upload PDF =====
  const handleUpload = async (file) => {
    if (!file) return alert("Select a PDF first");
    const formData = new FormData();
    formData.append("file", file);
    try {
      await axios.post(`${API_BASE}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      await fetchDocuments();
      alert("File uploaded successfully");
    } catch (err) {
      console.error(err);
      alert("Upload failed");
    }
  };

  // ===== Fetch rules from PDF (backend extraction) =====
  const fetchRulesFromPDF = async () => {
    if (!selectedDoc) return alert("Select a document first");
    try {
      const res = await axios.post(`${API_BASE}/fetch_rules/${selectedDoc}`);
      alert("Rules extracted and saved");
      fetchRules(selectedDoc);
    } catch (err) {
      console.error(err);
      alert("Failed to extract rules");
    }
  };

  // ===== Add Rule =====
  const handleAddRule = async () => {
    if (!selectedDoc || !newRule.trim()) return alert("Enter a rule");
    try {
      await axios.post(`${API_BASE}/rules`, null, {
        params: { filename: selectedDoc, rule_type: newType, rule_value: newRule },
      });
      setNewRule("");
      fetchRules(selectedDoc);
    } catch (err) {
      console.error(err);
      alert("Failed to add rule");
    }
  };

  // ===== Delete Rule =====
  const handleDeleteRule = async (type, value) => {
    if (!selectedDoc) return;
    try {
      await axios.delete(`${API_BASE}/rules`, {
        params: { filename: selectedDoc, rule_type: type, rule_value: value },
      });
      fetchRules(selectedDoc);
    } catch (err) {
      console.error(err);
      alert("Failed to delete rule");
    }
  };

  // ===== Run RAG Query =====
  const runQuery = async () => {
    if (!selectedDoc || !query.trim()) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/rag/${selectedDoc}`, { query });
      setResponse({ query, ...res.data });
    } catch (err) {
      console.error(err);
      alert("Query failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 pt-24 p-8 text-white">
      <header className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-2 text-white">
          <ShieldCheck className="w-7 h-7 text-blue-400" />
          Compliance
        </h1>
        <p className="text-gray-400 mt-1">
          Manage compliance rules, upload policy documents, and test safe execution.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* ===== Left Column: Upload + Documents ===== */}
        <div className="space-y-6">
          <div className="card bg-gray-900 shadow-md border border-gray-700">
            <div className="card-body text-white">
              <h2 className="card-title flex items-center gap-2 text-white">
                <UploadCloud className="w-5 h-5 text-blue-400" />
                Upload PDF
              </h2>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => handleUpload(e.target.files[0])}
                className="mt-3 file-input file-input-bordered w-full bg-gray-800 text-gray-300 border-gray-600"
              />
              <button
                onClick={fetchRulesFromPDF}
                disabled={!selectedDoc}
                className="mt-3 btn bg-blue-600 hover:bg-blue-700 border-none text-white"
              >
                Extract Rules
              </button>
            </div>
          </div>

          <div className="card bg-gray-900 shadow-md border border-gray-700">
            <div className="card-body text-white">
              <h2 className="card-title flex items-center gap-2 text-white">
                <FileText className="w-5 h-5 text-blue-400" />
                Uploaded Documents
              </h2>
              <ul className="mt-4 space-y-2">
                {docs.length > 0 ? (
                  docs.map((doc) => (
                    <li key={doc}>
                      <button
                        onClick={() => setSelectedDoc(doc)}
                        className={`w-full text-left px-4 py-2 rounded-lg ${
                          selectedDoc === doc
                            ? "bg-blue-600 text-white"
                            : "bg-gray-800 hover:bg-gray-700 text-gray-300"
                        }`}
                      >
                        {doc}
                      </button>
                    </li>
                  ))
                ) : (
                  <li className="text-sm text-gray-400">No documents uploaded</li>
                )}
              </ul>
            </div>
          </div>
        </div>

        {/* ===== Middle Column: Compliance Viewer + RAG ===== */}
        <div className="lg:col-span-2 space-y-8">
          <div className="card bg-gray-900 shadow-md border border-gray-700 text-white">
            <div className="card-body">
              <h2 className="card-title flex items-center gap-2 text-white">
                <ShieldCheck className="w-5 h-5 text-blue-400" />
                Compliance Rules
              </h2>

              <div className="mt-6 grid md:grid-cols-3 gap-4">
                {["allowed", "forbidden", "required"].map((type) => (
                  <div key={type} className="border rounded-lg p-4 bg-gray-800 border-gray-700">
                    <h3 className="font-semibold capitalize mb-2 text-white">{type}</h3>
                    <ul className="space-y-1 text-sm">
                      {(rules[type] || []).length > 0 ? (
                        rules[type].map((r, idx) => (
                          <li
                            key={idx}
                            className="flex justify-between items-center bg-gray-900 p-2 rounded-md border border-gray-700"
                          >
                            <span className="text-gray-200">{r}</span>
                            <button
                              className="text-red-400 text-xs"
                              onClick={() => handleDeleteRule(type, r)}
                            >
                              Delete
                            </button>
                          </li>
                        ))
                      ) : (
                        <li className="text-gray-500 text-sm">No rules</li>
                      )}
                    </ul>
                  </div>
                ))}
              </div>

              {/* Add Rule */}
              <div className="mt-6 flex flex-wrap gap-3 items-center">
                <input
                  type="text"
                  placeholder="Enter new rule..."
                  value={newRule}
                  onChange={(e) => setNewRule(e.target.value)}
                  className="input input-bordered w-full md:w-1/2 bg-gray-800 text-gray-200 border-gray-600"
                />
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value)}
                  className="select select-bordered bg-gray-800 text-gray-200 border-gray-600"
                >
                  <option value="forbidden">forbidden</option>
                  <option value="allowed">allowed</option>
                  <option value="required">required</option>
                </select>
                <button
                  onClick={handleAddRule}
                  disabled={!selectedDoc || !newRule.trim()}
                  className="btn bg-blue-600 hover:bg-blue-700 border-none text-white"
                >
                  Add
                </button>
              </div>
            </div>
          </div>

          {/* RAG Simulation */}
          <div className="card bg-gray-900 shadow-md border border-gray-700 text-white">
            <div className="card-body">
              <h2 className="card-title flex items-center gap-2 text-white">
                <Zap className="w-5 h-5 text-blue-400" />
                Test RAG Compliance
              </h2>

              <div className="mt-4 flex gap-3 flex-wrap">
                <input
                  type="text"
                  placeholder="Enter your query..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="input input-bordered w-full md:w-2/3 bg-gray-800 text-gray-200 border-gray-600"
                />
                <button
                  onClick={runQuery}
                  disabled={loading}
                  className="btn bg-blue-600 hover:bg-blue-700 border-none text-white"
                >
                  {loading ? "Running..." : "Run Query"}
                </button>
              </div>

              {response && (
                <div className="mt-6 p-4 bg-gray-800 rounded-lg max-h-[400px] overflow-y-auto text-sm border border-gray-700">
                  <h3 className="font-semibold text-white">Query</h3>
                  <pre className="text-gray-300">{response.query}</pre>

                  <h3 className="font-semibold mt-2 text-white">Response</h3>
                  <pre className="text-gray-300">{JSON.stringify(response, null, 2)}</pre>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
