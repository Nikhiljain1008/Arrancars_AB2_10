// import React, { useState, useEffect } from 'react';
// import axios from 'axios';
// import { io } from 'socket.io-client';

// const Upload = () => {
//   const [file, setFile] = useState(null);
//   const [result, setResult] = useState(null);
//   const [error, setError] = useState(null);
//   const [alert, setAlert] = useState(null);
//   const [redactionLevel, setRedactionLevel] = useState('basic'); // State for redaction level

//   // Connect to the WebSocket server
//   const socket = io('http://127.0.0.1:5000');

//   useEffect(() => {
//     // Listen for real-time alerts
//     socket.on('pii_detected', (data) => {
//       setAlert(`PII Detected: ${JSON.stringify(data.detected_pii)}`);
//     });

//     // Clean up the socket connection
//     return () => {
//       socket.disconnect();
//     };
//   }, []);

//   const handleFileChange = (e) => {
//     setFile(e.target.files[0]);
//   };

//   const handleRedactionLevelChange = (e) => {
//     setRedactionLevel(e.target.value); // Update redaction level state
//   };

//   const handleSubmit = async () => {
//     if (!file) {
//       setError("Please select a file.");
//       return;
//     }

//     const formData = new FormData();
//     formData.append('file', file);
//     formData.append('redaction_level', redactionLevel); // Add redaction level to form data

//     try {
//       const response = await axios.post('http://127.0.0.1:5000/upload', formData, {
//         headers: {
//           'Content-Type': 'multipart/form-data',
//         },
//       });
//       setResult(response.data);
//       setError(null);
//     } catch (error) {
//       setError("Error uploading file. Please try again.");
//       console.error("Error details:", error.response ? error.response.data : error.message);
//     }
//   };

//   return (
//     <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
//       <h1>Upload Document</h1>
//       <input type="file" onChange={handleFileChange} />
      
//       {/* Redaction Level Dropdown */}
//       <div style={{ marginTop: '10px' }}>
//         <label htmlFor="redactionLevel">Redaction Level: </label>
//         <select
//           id="redactionLevel"
//           value={redactionLevel}
//           onChange={handleRedactionLevelChange}
//           style={{ padding: '5px', borderRadius: '5px' }}
//         >
//           <option value="basic">Basic</option>
//           <option value="intermediate">Intermediate</option>
//           <option value="critical">Critical</option>
//         </select>
//       </div>

//       <button onClick={handleSubmit} style={{ marginTop: '10px', padding: '10px' }}>
//         Upload
//       </button>

//       {error && <p style={{ color: 'red' }}>{error}</p>}
//       {alert && <p style={{ color: 'blue' }}>{alert}</p>}

//       {result && (
//         <div style={{ marginTop: '20px' }}>
//           <h2>Original Text</h2>
//           <pre style={{ whiteSpace: 'pre-wrap', background: '#f9f9f9', padding: '10px', borderRadius: '5px' }}>
//             {result.text}
//           </pre>

//           <h2>Redacted Text</h2>
//           <pre style={{ whiteSpace: 'pre-wrap', background: '#f9f9f9', padding: '10px', borderRadius: '5px' }}>
//             {result.redacted_text}
//           </pre>

//           <h2>Detected PII Details</h2>
//           <ul style={{ listStyleType: 'none', padding: '0' }}>
//             {Object.entries(result.detected_pii).map(([pii_type, values]) => (
//               <li key={pii_type} style={{ marginBottom: '10px' }}>
//                 <strong style={{ textTransform: 'capitalize' }}>{pii_type}:</strong>
//                 <ul style={{ listStyleType: 'none', paddingLeft: '20px' }}>
//                   {values.map((value, index) => (
//                     <li key={index}>{value}</li>
//                   ))}
//                 </ul>
//               </li>
//             ))}
//           </ul>

//           <h2>Download Redacted Document</h2>
//           <a href={`http://127.0.0.1:5000${result.redacted_file_url}`} download>
//             <button style={{ marginTop: '10px', padding: '10px' }}>
//               Download Redacted File
//             </button>
//           </a>
//         </div>
//       )}
//     </div>
//   );
// };

// export default Upload;
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { io } from 'socket.io-client';
import './upload.css'; // Import the CSS file for styling

const Upload = () => {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [alert, setAlert] = useState(null);
  const [redactionLevel, setRedactionLevel] = useState('basic'); // State for redaction level
  const [isLoading, setIsLoading] = useState(false); // Loading state
  const [isTranscribing, setIsTranscribing] = useState(false); // State for live transcription
  const [transcription, setTranscription] = useState(''); // State for transcribed text
  const [transcriptionPII, setTranscriptionPII] = useState([]); // State for detected PII in transcription

  // Connect to the WebSocket server
  const socket = io('http://127.0.0.1:5000', {
    reconnection: true, // Enable reconnection
    reconnectionAttempts: 5, // Number of reconnection attempts
    reconnectionDelay: 1000, // Delay between reconnection attempts
  });

  useEffect(() => {
    // Listen for real-time alerts from file upload
    socket.on('pii_detected', (data) => {
      setAlert(`PII Detected: ${JSON.stringify(data.detected_pii)}`);
    });

    // Listen for real-time alerts from live transcription
    socket.on('pii_audio_detected', (data) => {
      setTranscriptionPII((prev) => [...prev, data]); // Add detected PII to the list
      playAlertSound(); // Play a sound when PII is detected
    });

    // Handle connection errors
    socket.on('connect_error', (err) => {
      console.error('WebSocket connection error:', err);
      setAlert('Failed to connect to the server. Please refresh the page.');
    });

    // Clean up the socket connection
    return () => {
      socket.disconnect();
    };
  }, []);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null); // Clear any previous errors
  };

  const handleRedactionLevelChange = (e) => {
    setRedactionLevel(e.target.value); // Update redaction level state
  };

  const handleSubmit = async () => {
    if (!file) {
      setError("Please select a file.");
      return;
    }

    setIsLoading(true); // Start loading
    setError(null); // Clear previous errors
    setResult(null); // Clear previous results

    const formData = new FormData();
    formData.append('file', file);
    formData.append('redaction_level', redactionLevel); // Add redaction level to form data

    try {
      const response = await axios.post('http://127.0.0.1:5000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResult(response.data);
      setAlert(null); // Clear any previous alerts
    } catch (error) {
      setError("Error uploading file. Please try again.");
      console.error("Error details:", error.response ? error.response.data : error.message);
    } finally {
      setIsLoading(false); // Stop loading
    }
  };

  const startTranscription = async () => {
    setIsTranscribing(true);
    setTranscription(''); // Clear previous transcription
    setTranscriptionPII([]); // Clear previous PII detections

    try {
      const response = await axios.get('http://127.0.0.1:5000/live_transcription');
      console.log('Transcription started:', response.data);
    } catch (error) {
      setError("Error starting live transcription. Please try again.");
      console.error("Error details:", error.response ? error.response.data : error.message);
    }
  };

  const stopTranscription = () => {
    setIsTranscribing(false);
    console.log('Transcription stopped.');
  };

  const playAlertSound = () => {
    const audio = new Audio('/path/to/alert-sound.mp3'); // Replace with the path to your alert sound
    audio.play();
  };

  return (
    <div className="upload-container">
      <h1>Document Redaction Tool</h1>
      <div className="upload-box">
        <input
          type="file"
          id="fileInput"
          onChange={handleFileChange}
          className="file-input"
        />
        <label htmlFor="fileInput" className="file-label">
          Choose File
        </label>

        <div className="redaction-level">
          <label htmlFor="redactionLevel">Redaction Level: </label>
          <select
            id="redactionLevel"
            value={redactionLevel}
            onChange={handleRedactionLevelChange}
            className="level-select"
          >
            <option value="basic">Basic</option>
            <option value="intermediate">Intermediate</option>
            <option value="critical">Critical</option>
          </select>
        </div>

        <button onClick={handleSubmit} className="upload-button" disabled={isLoading}>
          {isLoading ? 'Processing...' : 'Upload and Redact'}
        </button>

        {error && <p className="error-message">{error}</p>}
        {alert && (
          <div className="alert-message">
            <strong>Alert:</strong> {alert}
          </div>
        )}
      </div>

      {/* Live Transcription Section */}
      <div className="transcription-box">
        <h2>Live Transcription</h2>
        <button
          onClick={isTranscribing ? stopTranscription : startTranscription}
          className="transcription-button"
        >
          {isTranscribing ? 'Stop Transcription' : 'Start Transcription'}
        </button>

        {isTranscribing && (
          <div className="transcription-results">
            <h3>Transcribed Text</h3>
            <pre className="text-box">{transcription}</pre>

            <h3>Detected PII in Transcription</h3>
            <ul className="pii-list">
              {transcriptionPII.map((pii, index) => (
                <li key={index} className="pii-item">
                  <strong className="pii-type">{pii.type}:</strong> {pii.value}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {result && (
        <div className="result-container">
          <h2>Original Text</h2>
          <pre className="text-box">{result.text}</pre>

          <h2>Redacted Text</h2>
          <pre className="text-box">{result.redacted_text}</pre>

          <h2>Detected PII Details</h2>
          <ul className="pii-list">
            {Object.entries(result.detected_pii).map(([pii_type, values]) => (
              <li key={pii_type} className="pii-item">
                <strong className="pii-type">{pii_type}:</strong>
                <ul className="pii-values">
                  {values.map((value, index) => (
                    <li key={index} className="pii-value">{value}</li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>

          {result.redacted_file_url && (
            <>
              <h2>Download Redacted Document</h2>
              <a
                href={`http://127.0.0.1:5000${result.redacted_file_url}`}
                download
                className="download-link"
              >
                <button className="download-button">Download Redacted File</button>
              </a>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default Upload;