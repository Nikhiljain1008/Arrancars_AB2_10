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
  const [detectionTimeline, setDetectionTimeline] = useState([]); // State for detection timeline

  // Initialize socket with immediate connection
  const socket = io('http://127.0.0.1:5000', {
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
  });

  // Set up socket event listeners once when component mounts
  useEffect(() => {

      // Debug: Log socket connection status
    socket.on('connect', () => {
      console.log('✅ Socket Connected');
    });

    socket.on('disconnect', () => {
      console.log('❌ Socket Disconnected');
    });

    // Listen for real-time alerts from file upload
    socket.on('pii_detected', (data) => {
      console.log("📥 Received pii_detected:", data);
      setAlert(`PII Detected: ${JSON.stringify(data.detected_pii)}`);
    });

    // Listen for real-time alerts from live transcription
    socket.on('pii_alert', (data) => {
      console.log("📥 Received pii_alert:", data);
      setTranscriptionPII((prev) => [...prev, data]);
      playAlertSound();

      // Add detection to timeline
      setDetectionTimeline((prev) => [
        ...prev,
        {
          time: new Date().toLocaleTimeString(),
          type: data.type,
          value: data.value,
        },
      ]);
    });

    // Listen for transcription updates
    socket.on('transcription_update', (data) => {
      console.log("📥 Received transcription_update:", data);
      setTranscription((prev) => prev + '\n' + data.text);
    });

    // When transcription completes
    socket.on('transcription_complete', () => {
      console.log("📥 Received transcription_complete");
      setIsTranscribing(false);
      stopTranscription();
    });

    // Handle connection errors
    socket.on('connect_error', (err) => {
      console.error('WebSocket connection error:', err);
      setAlert('Failed to connect to the server. Please refresh the page.');
    });

    return () => {
      socket.off('pii_detected');
      socket.off('pii_alert');
      socket.off('transcription_update');
      socket.off('transcription_complete');
      socket.off('connect_error');
    };
  }, [isTranscribing]);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
  };

  const handleRedactionLevelChange = (e) => {
    setRedactionLevel(e.target.value);
  };

  const handleSubmit = async () => {
    if (!file) {
      setError('Please select a file.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('redaction_level', redactionLevel);

    try {
      const response = await axios.post('http://127.0.0.1:5000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResult(response.data);
      setAlert(null);
    } catch (error) {
      setError('Error uploading file. Please try again.');
      console.error('Error details:', error.response ? error.response.data : error.message);
    } finally {
      setIsLoading(false);
    }
  };

  // 🔹 Use WebSocket instead of axios for live transcription
  const startTranscription = () => {
    console.log('🎤 Starting transcription...');
    setIsTranscribing(true);
    setTranscription('');
    setTranscriptionPII([]);
    setDetectionTimeline([]);

    // Emit the start event
    socket.emit('start_transcription', {}, (response) => {
      // Optional: Handle acknowledgment
      console.log('start_transcription acknowledged:', response);
    });
  };

  const stopTranscription = () => {
    console.log('🛑 Stopping transcription...');
    setIsTranscribing(false);
    
    // Emit a stop event if needed
    socket.emit('stop_transcription', {}, (response) => {
      // Optional: Handle acknowledgment
      console.log('stop_transcription acknowledged:', response);
    });
  };

  const playAlertSound = () => {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.type = 'sine';
    oscillator.frequency.value = 880;
    gainNode.gain.value = 0.3;

    oscillator.start();

    setTimeout(() => {
      oscillator.stop();
      audioContext.close();
    }, 200);
  };

  return (
    <div className="upload-container">
      <h1>Document Redaction Tool</h1>
      <div className="upload-box">
        <input type="file" id="fileInput" onChange={handleFileChange} className="file-input" />
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
      <div className="transcription-container">
        <h2>Live Transcription</h2>

        <div className="controls">
          <button
            onClick={isTranscribing ? stopTranscription : startTranscription}
            className={isTranscribing ? 'stop-button' : 'start-button'}
          >
            {isTranscribing ? 'Stop Listening' : 'Start Listening'}
          </button>
        </div>

        {isTranscribing && (
          <>
            <div className="listening-indicator">
              <div className="mic-icon"></div>
              <span className="listening-text">Listening...</span>
            </div>

            <div className="live-transcript">{transcription}</div>

            {transcriptionPII.length > 0 && (
              <div className="detection-alert">
                <span role="img" aria-label="warning">
                  ⚠️
                </span>
                <div>
                  <strong>Sensitive Information Detected!</strong>
                  <p>Last detection: {transcriptionPII[transcriptionPII.length - 1]?.type}</p>
                </div>
              </div>
            )}

            <div className="detection-timeline">
              <h3>Detection Timeline</h3>
              {detectionTimeline.map((detection, index) => (
                <div key={index} className="timeline-item">
                  <div className="timeline-time">{detection.time}</div>
                  <div className="timeline-content">
                    <strong>{detection.type}</strong>: {detection.value}
                  </div>
                </div>
              ))}
            </div>
          </>
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
