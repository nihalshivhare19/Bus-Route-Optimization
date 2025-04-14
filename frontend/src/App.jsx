import React, { useState } from "react";
import UploadForm from "./components/UploadForm";
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import MapDisplay from "./components/MapDisplay";

function App() {
  const [mapHtml, setMapHtml] = useState("");

  const handleMapLoaded = (html) => {
    setMapHtml(html);
  };

  return (
    <div>
      {/* <h1>Route Planner</h1> */}
      <UploadForm onMapLoaded={handleMapLoaded} />
      {mapHtml && <MapDisplay mapHtml={mapHtml} />}
      
    </div>
  );
}

export default App;
