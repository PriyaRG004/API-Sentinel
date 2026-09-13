import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);

  const [apiName, setApiName] = useState("");
  const [apiUrl, setApiUrl] = useState("");
  const [message, setMessage] = useState("");

  const [history, setHistory] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);

  const fetchDashboard = async () => {
    try {
      setLoading(true);

      const response = await fetch(
        "http://127.0.0.1:8000/dashboard"
      );

      if (!response.ok) {
        throw new Error("Failed to fetch dashboard");
      }

      const data = await response.json();

      setDashboard(data);
    } catch (error) {
      console.error("Error:", error);
      setDashboard(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  // ADD API
  const addApi = async (event) => {
    event.preventDefault();

    if (!apiName || !apiUrl) {
      setMessage("Please enter both API name and URL.");
      return;
    }

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/apis",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: apiName,
            url: apiUrl,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error("Failed to add API");
      }

      setMessage(data.message);

      setApiName("");
      setApiUrl("");

      await fetchDashboard();
    } catch (error) {
      console.error("Error:", error);
      setMessage("Failed to add API.");
    }
  };

  // DELETE API
  const deleteApi = async (apiId) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this API?"
    );

    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/apis/${apiId}`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error("Failed to delete API");
      }

      setMessage(data.message);

      await fetchDashboard();
    } catch (error) {
      console.error("Error:", error);
      setMessage("Failed to delete API.");
    }
  };
  // ACTIVATE / DEACTIVATE API
const toggleApi = async (api) => {
  try {
    const response = await fetch(
      `http://127.0.0.1:8000/apis/${api.id}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          active: !api.active,
        }),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error("Failed to update API status");
    }

    setMessage(data.message);

    await fetchDashboard();
  } catch (error) {
    console.error("Toggle error:", error);
    setMessage("Failed to update API status.");
  }
};

  // VIEW HISTORY
  const viewHistory = async (apiId) => {
    try {
      setHistoryLoading(true);

      const response = await fetch(
        `http://127.0.0.1:8000/apis/${apiId}/history`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch history");
      }

      const data = await response.json();

      setHistory(data);
    } catch (error) {
      console.error("History error:", error);
      setMessage("Failed to load API history.");
    } finally {
      setHistoryLoading(false);
    }
  };

  // CLOSE HISTORY
  const closeHistory = () => {
    setHistory(null);
  };

  if (loading) {
    return (
      <div className="loading">
        <h2>Loading API Sentinel...</h2>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="loading">
        <h2>Unable to connect to backend</h2>

        <p>Make sure FastAPI is running.</p>

        <button onClick={fetchDashboard}>
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="app">

      {/* HEADER */}

      <header className="header">

        <div>
          <h1>API Sentinel</h1>

          <p>
            API Monitoring Dashboard
          </p>
        </div>

        <button
          className="refresh-button"
          onClick={fetchDashboard}
        >
          Refresh
        </button>

      </header>

      {/* SUMMARY */}

      <div className="summary">

  <div className="card">
    <h3>Total APIs</h3>
    <p>
      {dashboard.summary.total}
    </p>
  </div>

  <div className="card">
    <h3>APIs UP</h3>
    <p className="up-number">
      {dashboard.summary.up}
    </p>
  </div>

  <div className="card">
    <h3>APIs DOWN</h3>
    <p className="down-number">
      {dashboard.summary.down}
    </p>
  </div>

  <div className="card">
    <h3>Inactive APIs</h3>
    <p>
      {dashboard.summary.total -
        dashboard.summary.active}
    </p>
  </div>

</div>

      {/* ADD API */}

      <section className="add-section">

        <h2>Add New API</h2>

        <form
          onSubmit={addApi}
          className="add-form"
        >

          <input
            type="text"
            placeholder="API Name"
            value={apiName}
            onChange={(event) =>
              setApiName(event.target.value)
            }
          />

          <input
            type="url"
            placeholder="API URL"
            value={apiUrl}
            onChange={(event) =>
              setApiUrl(event.target.value)
            }
          />

          <button type="submit">
            Add API
          </button>

        </form>

        {message && (
          <p className="message">
            {message}
          </p>
        )}

      </section>

      {/* API TABLE */}

      <section className="api-section">

        <h2>Monitored APIs</h2>

        <table>

          <thead>

            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>URL</th>
              <th>Status</th>
              <th>Status Code</th>
              <th>Response Time</th>
              <th>Actions</th>
            </tr>

          </thead>

          <tbody>

            {dashboard.apis.map((api) => (

              <tr key={api.id}>

                <td>
                  {api.id}
                </td>

                <td className="api-name">
                  {api.name}
                </td>

                <td className="api-url">
                  {api.url}
                </td>

                <td>

                  <span
  className={
    api.status === "UP"
      ? "status-up"
      : api.status === "DOWN"
      ? "status-down"
      : "status-inactive"
  }
>
  {api.status}
</span>

                </td>

                <td>
                  {api.status_code || "-"}
                </td>

                <td>
                  {api.response_time
                    ? `${api.response_time.toFixed(2)} sec`
                    : "-"}
                </td>
                

                <td className="actions">

                  <button
                    className="history-button"
                    onClick={() =>
                      viewHistory(api.id)
                    }
                  >
                    History
                  </button>
                  <button
    className="toggle-button"
    onClick={() => toggleApi(api)}
  >
    {api.active ? "Disable" : "Enable"}
  </button>
                  

                  <button
                    className="delete-button"
                    onClick={() =>
                      deleteApi(api.id)
                    }
                  >
                    Delete
                  </button>

                </td>

              </tr>

            ))}

          </tbody>

        </table>

      </section>

      {/* HISTORY */}

      {history && (

        <section className="history-section">

          <div className="history-header">

            <div>

              <h2>
                API History
              </h2>

              <p>
                <strong>
                  {history.name}
                </strong>
              </p>

              <p className="history-url">
                {history.url}
              </p>

            </div>

            <button
              onClick={closeHistory}
            >
              Close
            </button>

          </div>

          {historyLoading ? (

            <p>
              Loading history...
            </p>

          ) : history.history.length === 0 ? (

            <p>
              No monitoring history available.
            </p>

          ) : (

            <table>

              <thead>

                <tr>
                  <th>Status</th>
                  <th>Status Code</th>
                  <th>Response Time</th>
                  <th>Checked At</th>
                </tr>

              </thead>

              <tbody>

                {history.history.map(
                  (check, index) => (

                    <tr key={index}>

                      <td>

                        <span
                          className={
                            check.status === "UP"
                              ? "status-up"
                              : "status-down"
                          }
                        >
                          {check.status}
                        </span>

                      </td>

                      <td>
                        {check.status_code || "-"}
                      </td>

                      <td>
                        {check.response_time
                          ? `${check.response_time.toFixed(
                              2
                            )} sec`
                          : "-"}
                      </td>

                      <td>
                        {new Date(
                          check.checked_at
                        ).toLocaleString()}
                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          )}

        </section>

      )}

    </div>
  );
}

export default App;