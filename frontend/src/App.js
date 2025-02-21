import { useState } from "react";
import axios from "axios";
import "./index.css";

function App() {
    const [text, setText] = useState("");
    const [summary, setSummary] = useState("");
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);

    // Handle text input
    const handleTextChange = (e) => setText(e.target.value);

    // Handle file selection
    const handleFileChange = (e) => setFile(e.target.files[0]);

    // Unified function to summarise text or file
    const handleSummarise = async () => {
        setLoading(true);
        setSummary("");

        try {
            let response;
            
            if (file) {
                const formData = new FormData();
                formData.append("file", file);

                response = await axios.post("http://127.0.0.1:5000/upload", formData, {
                    headers: { "Content-Type": "multipart/form-data" }
                });
            } else if (text.trim()) {
                response = await axios.post("http://127.0.0.1:5000/summarise", { text });
            } else {
                alert("Please enter text or upload a file.");
                setLoading(false);
                return;
            }

            setSummary(response.data.summary);
        } catch (error) {
            console.error("Error:", error);
            alert("Failed to summarise. Ensure the backend is running.");
        }

        setLoading(false);
    };

    return (
        <div className="container">
            <h1>Briefly AI</h1>

            <textarea
                placeholder="Enter text to summarise (or upload a file below)..."
                value={text}
                onChange={handleTextChange}
            />

            <label className="file-upload">
                <input type="file" accept=".pdf,.docx,.txt" onChange={handleFileChange} />
                {file ? file.name : "Choose a file"}
            </label>

            <button onClick={handleSummarise} disabled={loading}>
                {loading ? "Summarising..." : "Summarise..."}
            </button>

            {summary && (
                <div className="summary-box">
                    <strong>Summary:</strong> {summary}
                </div>
            )}
        </div>
    );
}

export default App;
