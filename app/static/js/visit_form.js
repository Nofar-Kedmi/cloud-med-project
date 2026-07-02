document.addEventListener("DOMContentLoaded", () => {
    const researchBtn = document.getElementById("medical-research-btn");
    const diagnosisField = document.getElementById("diagnosis");
    const resultsPanel = document.getElementById("research-results");

    if (!researchBtn || !diagnosisField || !resultsPanel || !window.MEDICAL_RESEARCH_URL) {
        return;
    }

    researchBtn.addEventListener("click", async () => {
        const diagnosis = diagnosisField.value.trim();
        if (!diagnosis) {
            showResearchMessage("Please enter a diagnosis before searching.", false);
            return;
        }

        researchBtn.disabled = true;
        researchBtn.textContent = "Searching...";

        try {
            const response = await fetch(
                `${window.MEDICAL_RESEARCH_URL}?diagnosis=${encodeURIComponent(diagnosis)}`,
                { headers: { Accept: "application/json" } }
            );
            const data = await response.json();
            renderResearchResults(data);
        } catch (error) {
            showResearchMessage("Unable to fetch medical research. Please try again.", false);
        } finally {
            researchBtn.disabled = false;
            researchBtn.textContent = "Medical Research";
        }
    });

    function showResearchMessage(message, isSuccess) {
        resultsPanel.classList.remove("hidden");
        resultsPanel.innerHTML = `<p class="${isSuccess ? "research-summary" : "research-error"}">${escapeHtml(message)}</p>`;
    }

    function renderResearchResults(data) {
        resultsPanel.classList.remove("hidden");

        if (!data.available) {
            showResearchMessage(data.message || "Research is unavailable.", false);
            return;
        }

        const items = (data.results || [])
            .map(
                (item) => `
                <article class="research-item">
                    <a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.title)}</a>
                    <p>${escapeHtml(item.content || "")}</p>
                </article>
            `
            )
            .join("");

        resultsPanel.innerHTML = `
            <h3>Medical Research</h3>
            <p class="research-summary">${escapeHtml(data.message || "")}</p>
            ${items || "<p>No articles found for this diagnosis.</p>"}
        `;
    }

    function escapeHtml(value) {
        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }
});
