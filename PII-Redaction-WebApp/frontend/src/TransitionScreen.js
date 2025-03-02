import React, { useState, useEffect } from 'react';
import './TransitionScreen.css'; // Add CSS for the transition screen

const TransitionScreen = ({ onComplete }) => {
    const [text, setText] = useState('');
    const fullText = 'PII DETECTOR';
    const [index, setIndex] = useState(0);

    useEffect(() => {
        if (index < fullText.length) {
            const timeout = setTimeout(() => {
                setText((prev) => prev + fullText[index]);
                setIndex((prev) => prev + 1);
            }, 200); // Delay between letters (200ms)
            return () => clearTimeout(timeout);
        } else {
            // After all letters are revealed, wait for 1 second and then call onComplete
            const timeout = setTimeout(() => {
                onComplete();
            }, 1000);
            return () => clearTimeout(timeout);
        }
    }, [index, fullText, onComplete]);

    return (
        <div className="transition-screen">
            <h1 className="transition-text">
                {text.split('').map((char, i) => (
                    <span key={i} className="letter">
                        {char}
                    </span>
                ))}
            </h1>
        </div>
    );
};

export default TransitionScreen;