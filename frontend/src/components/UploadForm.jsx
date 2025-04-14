import React, { useState } from "react";

const UploadForm = ({ onMapLoaded }) => {
  const [file, setFile] = useState(null);
  const [numVehicles, setNumVehicles] = useState("");
  const [capacities, setCapacities] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type !== "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet") {
      alert("Please upload a valid Excel file (.xlsx).");
      return;
    }
    setFile(selectedFile);
  };
  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!file || !numVehicles || !capacities) {
      alert("All fields are required.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("numVehicles", numVehicles);
    formData.append("capacities", capacities);

    try {
      const response = await fetch("http://127.0.0.1:5000/process-data", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const mapHtml = await response.text();
        onMapLoaded(mapHtml);
      } else {
        alert("Failed to process data. Please try again.");
      }
    } catch (error) {
      console.error("Error:", error);
      alert("An error occurred while processing your request.");
    }
  };

  return (
    <div className="w3-container w3-blue">
    <div className="flex min-h-full flex-1 flex-col justify-center px-6 py-12 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-sm">
          <h2 className="mt-10 text-center text-2xl/9 font-bold tracking-tight text-gray-900">
          Route Planner
          </h2>
        </div>

        <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-sm">
          <form action="#" method="POST" className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="file-upload" className="block text-sm/6 font-medium text-gray-900">
                Upload Excel File :
              </label>
              <div className="mt-2">
                <input
                  id="file-upload"
                  name="file-upload"
                  type="file"
                  accept=".xlsx"
                  required
                  onChange={handleFileChange}
                  // autoComplete="email"
                  className="block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between">
                <label htmlFor="noOfVehicles" className="block text-sm/6 font-medium text-gray-900">
                  Number of Vehicles :
                </label>
              </div>
              <div className="mt-2">
                <input
                  id="noOoVehicles"
                  name="noOfVehicles"
                  type="number"
                  value={numVehicles}
                  onChange={(e) => setNumVehicles(e.target.value)}
                  required
                  className="block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between">
                <label htmlFor="VehiclesCap" className="block text-sm/6 font-medium text-gray-900">
                  Vehicle Capacities (comma-separated) :
                </label>
              </div>
              <div className="mt-2">
                <input
                  id="VehiclesCap"
                  name="VehiclesCap"
                  type="text"
                  value={capacities}
                  onChange={(e) => setCapacities(e.target.value)}
                  required
                  className="block w-full rounded-md bg-white px-3 py-1.5 text-base text-gray-900 outline outline-1 -outline-offset-1 outline-gray-300 placeholder:text-gray-400 focus:outline focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                className="flex w-full justify-center rounded-md bg-blue-600 px-3 py-1.5 text-sm/6 font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                disabled={isLoading}
              >
               {isLoading ? "Processing..." : "Submit"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default UploadForm;
