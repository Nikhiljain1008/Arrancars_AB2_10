import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { io } from 'socket.io-client';

const Upload = () => {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [alert, setAlert] = useState(null);

  // Connect to the WebSocket server
  const socket = io('http://127.0.0.1:5000');

  useEffect(() => {
    // Listen for real-time alerts
    socket.on('pii_detected', (data) => {
      setAlert(`PII Detected: ${JSON.stringify(data.detected_pii)}`);
    });

    // Clean up the socket connection
    return () => {
      socket.disconnect();
    };
  }, []);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async () => {
    if (!file) {
      setError("Please select a file.");
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://127.0.0.1:5000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResult(response.data);
      setError(null);
    } catch (error) {
      setError("Error uploading file. Please try again.");
      console.error("Error details:", error.response ? error.response.data : error.message);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Upload Document</h1>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleSubmit} style={{ marginTop: '10px', padding: '10px' }}>
        Upload
      </button>

      {error && <p style={{ color: 'red' }}>{error}</p>}
      {alert && <p style={{ color: 'blue' }}>{alert}</p>}

      {result && (
        <div style={{ marginTop: '20px' }}>
          <h2>Original Text</h2>
          <pre style={{ whiteSpace: 'pre-wrap', background: '#f9f9f9', padding: '10px', borderRadius: '5px' }}>
            {result.text}
          </pre>

          <h2>Redacted Text</h2>
          <pre style={{ whiteSpace: 'pre-wrap', background: '#f9f9f9', padding: '10px', borderRadius: '5px' }}>
            {result.redacted_text}
          </pre>

          <h2>Detected PII Details</h2>
          <ul style={{ listStyleType: 'none', padding: '0' }}>
            {Object.entries(result.detected_pii).map(([pii_type, values]) => (
              <li key={pii_type} style={{ marginBottom: '10px' }}>
                <strong style={{ textTransform: 'capitalize' }}>{pii_type}:</strong>
                <ul style={{ listStyleType: 'none', paddingLeft: '20px' }}>
                  {values.map((value, index) => (
                    <li key={index}>{value}</li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>

          <h2>Download Redacted Document</h2>
          <a href={`http://127.0.0.1:5000${result.redacted_file_url}`} download>
            <button style={{ marginTop: '10px', padding: '10px' }}>
              Download Redacted File
            </button>
          </a>
        </div>
      )}
    </div>
  );
};

export default Upload;