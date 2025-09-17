// import React from 'react';
// import TransitionScreen from './TransitionScreen';
// import Upload from './Upload';

// const App = () => {
//   const [transitionComplete, setTransitionComplete] = useState(false);

//   const handleTransitionComplete = () => {
//       setTransitionComplete(true);
//   };

//   return (
//       <div className="App">
//           {!transitionComplete ? (
//               <TransitionScreen onComplete={handleTransitionComplete} />
//           ) : (
//               <Upload />
//           )}
//       </div>
//   );
// };

// export default App;


import React, { useState } from 'react'; // Add useState here
import TransitionScreen from './TransitionScreen';
import Upload from './Upload';
// import './App.css';

const App = () => {
    const [transitionComplete, setTransitionComplete] = useState(false);

    const handleTransitionComplete = () => {
        setTransitionComplete(true);
    };

    return (
        <div className="App">
            {!transitionComplete ? (
                <TransitionScreen onComplete={handleTransitionComplete} />
            ) : (
                <Upload />
            )}
        </div>
    );
};

export default App;