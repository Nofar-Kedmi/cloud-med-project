(function () {
    function bindOcrOriginalToggle() {
        document.querySelectorAll(".ocr-toggle-original").forEach(function (button) {
            button.addEventListener("click", function () {
                const targetId = button.getAttribute("data-target");
                const field = targetId ? document.getElementById(targetId) : null;
                if (!field) {
                    return;
                }

                const correctedText = field.dataset.correctedText || field.value;
                const originalText = field.dataset.originalText || "";
                const showingOriginal = field.dataset.showingOriginal === "true";

                if (!originalText || originalText === correctedText) {
                    return;
                }

                if (showingOriginal) {
                    field.value = correctedText;
                    field.dataset.showingOriginal = "false";
                    button.textContent = "Show Original";
                } else {
                    if (!field.dataset.correctedText) {
                        field.dataset.correctedText = field.value;
                    }
                    field.value = originalText;
                    field.dataset.showingOriginal = "true";
                    button.textContent = "Show Corrected";
                }
            });
        });
    }

    function updateOcrFields(prescriptionId, payload) {
        const ocrField = document.getElementById("ocr_" + prescriptionId);
        const medicationField = document.getElementById("medication_" + prescriptionId);
        const toggleButton = document.querySelector(
            '.ocr-toggle-original[data-target="ocr_' + prescriptionId + '"]'
        );

        const correctedText =
            payload.full_ocr_text ||
            payload.extracted_text ||
            payload.corrected_text ||
            "";
        const originalText =
            payload.original_ocr_text ||
            payload.raw_text ||
            correctedText;

        if (ocrField) {
            ocrField.value = correctedText;
            ocrField.dataset.correctedText = correctedText;
            ocrField.dataset.originalText = originalText;
            ocrField.dataset.showingOriginal = "false";
        }

        if (toggleButton) {
            if (originalText && originalText !== correctedText) {
                toggleButton.hidden = false;
                toggleButton.textContent = "Show Original";
            } else {
                toggleButton.hidden = true;
            }
        }

        if (medicationField && payload.medication_name) {
            medicationField.value = payload.medication_name;
        }

        if (ocrField) {
            ocrField.focus();
            ocrField.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    }

    function formatValidationError(payload) {
        const baseMessage =
            payload.message || "This image does not look like a prescription.";
        const reasons = payload.reasons || [];

        if (!reasons.length) {
            return baseMessage;
        }

        return (
            baseMessage +
            "\n\n" +
            reasons.map(function (reason) {
                return "- " + reason;
            }).join("\n")
        );
    }

    function bindManualUploadForms() {
        document.querySelectorAll(".manual-upload-form").forEach(function (form) {
            const input = form.querySelector(".manual-upload-input");
            const trigger = form.querySelector(".manual-upload-trigger");
            const endpoint = form.getAttribute("data-upload-endpoint");
            const prescriptionId = form.getAttribute("data-prescription-id");

            if (!input || !trigger || !endpoint || !prescriptionId) {
                return;
            }

            trigger.addEventListener("click", function () {
                input.click();
            });

            input.addEventListener("change", async function () {
                const file = input.files && input.files[0];
                if (!file) {
                    return;
                }

                const formData = new FormData();
                formData.append("prescription_id", prescriptionId);
                formData.append("image", file);

                trigger.disabled = true;
                const originalLabel = trigger.textContent;
                trigger.textContent = "Validating & OCR...";

                try {
                    const response = await fetch(endpoint, {
                        method: "POST",
                        headers: { Accept: "application/json" },
                        body: formData,
                    });

                    const payload = await response.json();
                    if (response.status === 400 && payload.is_document === false) {
                        window.alert(formatValidationError(payload));
                        return;
                    }

                    if (!response.ok || !payload.success) {
                        throw new Error(payload.message || "Upload failed.");
                    }

                    updateOcrFields(prescriptionId, payload);
                } catch (error) {
                    window.alert(
                        error.message || "Could not process the uploaded prescription image."
                    );
                } finally {
                    trigger.disabled = false;
                    trigger.textContent = originalLabel;
                    input.value = "";
                }
            });
        });
    }

    function bindSampleOcrForms() {
        document.querySelectorAll(".sample-ocr-form").forEach(function (form) {
            form.addEventListener("submit", async function (event) {
                const endpoint = form.getAttribute("data-ocr-endpoint");
                const prescriptionId = form.getAttribute("data-prescription-id");
                if (!endpoint || !prescriptionId) {
                    return;
                }

                event.preventDefault();

                const select = form.querySelector('[name="sample_file"]');
                const sampleFile = select ? select.value.trim() : "";
                if (!sampleFile) {
                    window.alert("Please select a sample prescription image.");
                    return;
                }

                const submitButton = form.querySelector('button[type="submit"]');

                if (submitButton) {
                    submitButton.disabled = true;
                    submitButton.textContent = "Running OCR...";
                }

                try {
                    const response = await fetch(endpoint, {
                        method: "POST",
                        headers: {
                            Accept: "application/json",
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({ sample_file: sampleFile }),
                    });

                    const payload = await response.json();
                    if (!response.ok || !payload.success) {
                        throw new Error(payload.message || "OCR request failed.");
                    }

                    updateOcrFields(prescriptionId, payload);
                } catch (error) {
                    window.alert(error.message || "Could not decode the sample prescription.");
                } finally {
                    if (submitButton) {
                        submitButton.disabled = false;
                        submitButton.textContent = "Load & Run OCR";
                    }
                }
            });
        });
    }

    document.querySelectorAll(".ocr-result-field").forEach(function (field) {
        if (!field.dataset.correctedText) {
            field.dataset.correctedText = field.value;
        }
    });

    bindOcrOriginalToggle();
    bindSampleOcrForms();
    bindManualUploadForms();

    const modal = document.getElementById("side-effects-modal");
    const modalBody = document.getElementById("side-effects-body");
    const modalTitle = document.getElementById("side-effects-title");

    if (!modal || !modalBody) {
        return;
    }

    function openModal() {
        modal.hidden = false;
        document.body.classList.add("modal-open");
    }

    function closeModal() {
        modal.hidden = true;
        document.body.classList.remove("modal-open");
    }

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    function renderList(title, items) {
        if (!items || !items.length) {
            return "";
        }

        const listItems = items
            .map(function (item) {
                const text = typeof item === "string" ? item : JSON.stringify(item);
                return "<li>" + escapeHtml(text) + "</li>";
            })
            .join("");

        return (
            "<div class='side-effects-block'>" +
            "<h4>" + escapeHtml(title) + "</h4>" +
            "<ul class='side-effects-list'>" + listItems + "</ul>" +
            "</div>"
        );
    }

    function renderTrials(studies) {
        if (!studies || !studies.length) {
            return "";
        }

        const cards = studies
            .map(function (study) {
                return (
                    "<article class='trial-card'>" +
                    "<strong>" + escapeHtml(study.title || "Untitled study") + "</strong>" +
                    "<p class='label-dim'>" +
                    escapeHtml(study.nct_id || "") +
                    (study.status ? " · " + escapeHtml(study.status) : "") +
                    "</p>" +
                    (study.conditions
                        ? "<p>" + escapeHtml(study.conditions) + "</p>"
                        : "") +
                    "</article>"
                );
            })
            .join("");

        return (
            "<div class='side-effects-block'>" +
            "<h4>Related Clinical Trials (ClinicalTrials.gov)</h4>" +
            cards +
            "</div>"
        );
    }

    function renderSideEffects(payload) {
        if (!payload.available) {
            return "<p class='modal-alert'>" + escapeHtml(payload.message || "No data available.") + "</p>";
        }

        let html = "<p class='label-dim'>" + escapeHtml(payload.message || "") + "</p>";
        const details = payload.details || {};

        if (details.source === "openfda") {
            html += renderList("Warnings", details.warnings);
            html += renderList("Adverse Reactions", details.adverse_reactions);
            html += renderList("Drug Interactions", details.drug_interactions);
        } else if (details.source === "tavily" && details.results) {
            html += "<div class='side-effects-block'><h4>Medical Literature</h4><ul class='side-effects-list'>";
            details.results.forEach(function (item) {
                html +=
                    "<li><strong>" +
                    escapeHtml(item.title || "Untitled") +
                    "</strong><br>" +
                    escapeHtml(item.content || "") +
                    "</li>";
            });
            html += "</ul></div>";
        }

        html += renderTrials(payload.clinical_trials || []);
        return html;
    }

    async function fetchSideEffects(medication) {
        modalTitle.textContent = "Side Effects — " + medication;
        modalBody.innerHTML = "<p class='label-dim'>Loading clinical information...</p>";
        openModal();

        try {
            const response = await fetch(
                "/pharmacist/api/side-effects?medication=" + encodeURIComponent(medication),
                { headers: { Accept: "application/json" } }
            );
            const payload = await response.json();
            modalBody.innerHTML = renderSideEffects(payload);
        } catch (error) {
            modalBody.innerHTML =
                "<p class='modal-alert'>Could not load side-effect information. Please try again.</p>";
        }
    }

    document.querySelectorAll(".side-effects-btn").forEach(function (button) {
        button.addEventListener("click", function () {
            const inputId = button.getAttribute("data-medication-input");
            const input = inputId ? document.getElementById(inputId) : null;
            const medication = input ? input.value.trim() : "";

            if (!medication) {
                window.alert("Enter a medication name before checking side effects.");
                return;
            }

            fetchSideEffects(medication);
        });
    });

    modal.querySelectorAll("[data-close-modal]").forEach(function (element) {
        element.addEventListener("click", closeModal);
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && !modal.hidden) {
            closeModal();
        }
    });
})();
