const form = document.getElementById("machine-form");
const input = document.getElementById("machine-id");
const status = document.getElementById("status");
const result = document.getElementById("result");

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const machineId = input.value.trim();
    if (!machineId) {
        return;
    }

    status.textContent = `Querying ${machineId}...`;
    result.hidden = true;

    try {
        const response = await fetch(
            `/api/machines/${encodeURIComponent(machineId)}`
        );

        if (response.status === 404) {
            status.textContent = `No current state found for ${machineId}.`;
            return;
        }

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const state = await response.json();
        status.textContent = `Current state for ${machineId}`;
        result.textContent = JSON.stringify(state, null, 2);
        result.hidden = false;
    } catch (error) {
        status.textContent = `Query failed: ${error.message}`;
    }
});
