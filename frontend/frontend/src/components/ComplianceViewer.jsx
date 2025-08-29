import { useState, useEffect } from "react";
import { listDocuments, extractRules } from "../api/api.js";

export default function ComplianceViewer() {
  const [docs, setDocs] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState("");
  const [rules, setRules] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [loadingRules, setLoadingRules] = useState(false);
  const [error, setError] = useState(null);

  // Fetch documents on mount
  useEffect(() => {
    const fetchDocs = async () => {
      try {
        setLoadingDocs(true);
        setError(null);
        const data = await listDocuments();
        const docArray = Array.isArray(data?.documents)
          ? data.documents
          : Array.isArray(data)
          ? data
          : [];
        setDocs(docArray);
      } catch (err) {
        console.error("Error loading documents:", err);
        setError("Failed to load documents.");
      } finally {
        setLoadingDocs(false);
      }
    };
    fetchDocs();
  }, []);

  // Fetch compliance rules
  const fetchRules = async () => {
    if (!selectedDoc) return;
    try {
      setLoadingRules(true);
      setError(null);
      const data = await extractRules(selectedDoc);
      setRules(Array.isArray(data?.rules) ? data.rules : []);
    } catch (err) {
      console.error("Error extracting rules:", err);
      setError("Failed to fetch compliance rules.");
    } finally {
      setLoadingRules(false);
    }
  };

  return (
    <div className="p-4 border rounded-lg mt-4">
      <h2 className="font-bold text-lg mb-2">Compliance Rules</h2>

      {/* Document Selector */}
      <div className="flex gap-2 mb-3">
        <select
          onChange={(e) => setSelectedDoc(e.target.value)}
          value={selectedDoc}
          className="border px-2 py-1 rounded flex-grow"
        >
          <option value="">Select Document</option>
          {docs.map((doc) => (
            <option key={doc.id} value={doc.id}>
              {doc.filename || `Document ${doc.id}`}
            </option>
          ))}
        </select>
        <button
          onClick={fetchRules}
          disabled={!selectedDoc || loadingRules}
          className="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600 disabled:opacity-50"
        >
          {loadingRules ? "Loading..." : "Fetch Rules"}
        </button>
      </div>

      {/* Loading / Error States */}
      {loadingDocs && <p className="text-gray-500">Loading documents...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {/* Rules Table */}
      {rules.length > 0 && (
        <table className="mt-4 border w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="border px-2 py-1 text-left">Section</th>
              <th className="border px-2 py-1 text-left">Clause</th>
              <th className="border px-2 py-1 text-left">Requirement</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((r, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="border px-2 py-1">{r?.section || "-"}</td>
                <td className="border px-2 py-1">{r?.clause || "-"}</td>
                <td className="border px-2 py-1">{r?.requirement || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* No rules found */}
      {!loadingRules && rules.length === 0 && selectedDoc && !error && (
        <p className="text-gray-500 mt-2">No rules found for this document.</p>
      )}
    </div>
  );
}
