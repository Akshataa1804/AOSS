import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Compliance from "./components/compliance";
 // import your Compliance component

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/compliance" />} />
        <Route path="/compliance" element={<Compliance />} />
        {/* You can add other routes here */}
      </Routes>
    </Router>
  );
}
