import re
import uuid
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

# הנחה: כאן יש לייבא את send_message מהמודול הרלוונטי
# מהדוגמה שלך לא ברור מאיפה היא מגיעה, אז ודא שהיא מיובאת כאן
from app.services.messaging_service import send_message 

from app.middleware.rbac import role_required
from app.services.document_validation_service import validate_prescription_document
from app.services.clinicaltrials_service import search_clinical_trials
from app.services.drug_info_service import get_medication_side_effects
from app.services.ocr_result_service import (
    OCRResultServiceError,
    get_latest_ocr_text_for_prescription,
    get_latest_ocr_bundle_for_prescription,
    get_ocr_results_for_prescription,
    save_ocr_result,
)
from app.services.ocr_service import extract_text_from_prescription
from app.services.pharmacist_service import (
    PharmacistServiceError,
    PrescriptionNotFoundError,
    find_patients,
    get_open_prescriptions,
    get_patient_by_patient_id,
    get_prescription,
    get_recently_dispensed_prescriptions,
    list_sample_prescription_files,
    mark_prescription_dispensed,
)

pharmacist_bp = Blueprint("pharmacist", __name__, url_prefix="/pharmacist")

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _project_root() -> Path:
    return Path(current_app.root_path).parent


def _uploads_dir() -> Path:
    path = _project_root() / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _test_prescriptions_dir() -> Path:
    path = _project_root() / "test_prescriptions"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_IMAGE_EXTENSIONS


def _verify_uploaded_image(image_path: Path) -> None:
    """Ensure the uploaded file is a readable image before Vision processing."""
    try:
        with Image.open(image_path) as image:
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise PharmacistServiceError(
            "The uploaded file is not a valid prescription image."
        ) from exc


def _resolve_sample_path(filename: str) -> Path:
    safe_name = secure_filename(filename)
    if not safe_name or safe_name != Path(filename).name:
        raise PharmacistServiceError("Invalid sample prescription filename.")

    sample_path = _test_prescriptions_dir() / safe_name
    if not sample_path.is_file() or not _allowed_file(safe_name):
        raise PharmacistServiceError(f"Sample prescription '{safe_name}' was not found.")

    return sample_path.resolve()


def _parse_medication_from_ocr(text: str) -> str:
    if not text:
        return ""

    patterns = (
        r"(?im)^\s*medication\s*:\s*(.+)$",
        r"(?im)^\s*drug\s*:\s*(.+)$",
        r"(?im)^\s*medicine\s*:\s*(.+)$",
        r"(?im)^\s*rx\s*:\s*(.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip().splitlines()[0].strip(" .,-")
    return ""


def _run_ocr_for_prescription(
    image_path: Path,
    prescription_id: str,
    *,
    image_filename: str,
) -> dict:
    ocr_result = extract_text_from_prescription(image_path)
    if not ocr_result.get("success"):
        raise PharmacistServiceError(
            ocr_result.get("error") or "OCR processing failed."
        )

    full_ocr_text = (
        ocr_result.get("full_ocr_text")
        or ocr_result.get("extracted_text")
        or ""
    ).strip()
    original_ocr_text = (
        ocr_result.get("original_ocr_text")
        or full_ocr_text
    ).strip()

    document_id = save_ocr_result(
        image_path,
        full_ocr_text,
        ocr_result["provider"],
        ocr_result["model"],
        prescription_id=prescription_id,
        pharmacist_id=current_user.get_id(),
        image_filename=image_filename,
        raw_text=original_ocr_text,
        original_ocr_text=original_ocr_text,
        ocr_corrections=list(ocr_result.get("ocr_corrections") or []),
    )

    prescription = get_prescription(prescription_id) or {}
    medication_name = (
        _parse_medication_from_ocr(full_ocr_text)
        or prescription.get("medication_name", "")
    )

    return {
        "success": True,
        "prescription_id": prescription_id,
        "document_id": document_id,
        "full_ocr_text": full_ocr_text,
        "original_ocr_text": original_ocr_text,
        "extracted_text": full_ocr_text,
        "was_corrected": bool(ocr_result.get("was_corrected")),
        "medication_name": medication_name,
    }


def _process_sample_ocr(prescription_id: str, sample_file: str) -> dict:
    if not sample_file:
        raise PharmacistServiceError("Please select a sample prescription image.")

    sample_path = _resolve_sample_path(sample_file)
    return _run_ocr_for_prescription(
        sample_path,
        prescription_id,
        image_filename=f"sample_{sample_path.name}",
    )


@pharmacist_bp.route("/search", methods=["GET", "POST"])
@login_required
@role_required("pharmacist")
def search():
    query = ""
    patients = []

    if request.method == "POST":
        query = (request.form.get("query") or request.form.get("id_number") or "").strip()
    else:
        query = (request.args.get("query") or request.args.get("id_number") or "").strip()

    if query:
        patients = find_patients(query)
        if not patients:
            flash(f"No patients found matching '{query}'.", "warning")

    return render_template(
        "pharmacist/search.html",
        query=query,
        patients=patients,
    )


@pharmacist_bp.route("/patient/<patient_id>/prescriptions")
@login_required
@role_required("pharmacist")
def prescriptions(patient_id):
    patient = get_patient_by_patient_id(patient_id)
    if not patient:
        flash("Patient not found.", "danger")
        return redirect(url_for("pharmacist.search"))

    open_prescriptions = get_open_prescriptions(patient_id)
    dispensed_prescriptions = (
        get_recently_dispensed_prescriptions(patient_id)
        if not open_prescriptions
        else []
    )
    sample_files = list_sample_prescription_files(_test_prescriptions_dir())
    active_rx = request.args.get("rx", "").strip()

    ocr_text_by_rx = {}
    ocr_original_by_rx = {}
    for rx in open_prescriptions:
        bundle = get_latest_ocr_bundle_for_prescription(rx["prescription_id"])
        ocr_text_by_rx[rx["prescription_id"]] = bundle["corrected_text"]
        ocr_original_by_rx[rx["prescription_id"]] = bundle["original_text"]

    return render_template(
        "pharmacist/prescriptions.html",
        patient=patient,
        prescriptions=open_prescriptions,
        sample_files=sample_files,
        ocr_text_by_rx=ocr_text_by_rx,
        ocr_original_by_rx=ocr_original_by_rx,
        dispensed_prescriptions=dispensed_prescriptions,
        active_rx=active_rx,
    )


@pharmacist_bp.route("/prescriptions/<prescription_id>/dispense", methods=["POST"])
@login_required
@role_required("pharmacist")
def dispense_prescription(prescription_id):
    prescription = get_prescription(prescription_id)
    if not prescription:
        flash("Prescription not found.", "danger")
        return redirect(url_for("pharmacist.search"))

    patient_id = prescription.get("patient_id", "")
    corrected_medication = (request.form.get("corrected_medication_name") or "").strip()
    verified_ocr_text = (request.form.get("verified_ocr_text") or "").strip()

    try:
        mark_prescription_dispensed(
            prescription_id,
            corrected_medication_name=corrected_medication or None,
            verified_ocr_text=verified_ocr_text or None,
            pharmacist_id=current_user.get_id(),
        )
        
        # התוספת המבוקשת
        send_message('medication-monitoring', {'med_name': 'Aspirin', 'status': 'checked'})
        
        flash(f"Prescription {prescription_id} marked as Dispensed.", "success")
    except PrescriptionNotFoundError:
        flash("Prescription not found.", "danger")
    except PharmacistServiceError as exc:
        flash(str(exc), "warning")

    return redirect(url_for("pharmacist.prescriptions", patient_id=patient_id))


@pharmacist_bp.route("/api/validate-and-ocr", methods=["POST"])
@login_required
@role_required("pharmacist")
def api_validate_and_ocr():
    prescription_id = (request.form.get("prescription_id") or "").strip()
    file = request.files.get("image")

    if not prescription_id:
        return jsonify({"success": False, "message": "Prescription id is required."}), 400

    prescription = get_prescription(prescription_id)
    if not prescription:
        return jsonify({"success": False, "message": "Prescription not found."}), 404

    if not file or not file.filename:
        return jsonify(
            {"success": False, "message": "Please select a prescription image to upload."}
        ), 400

    if not _allowed_file(file.filename):
        return jsonify(
            {"success": False, "message": "Allowed formats: JPG, PNG, WEBP."}
        ), 400

    safe_name = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    save_path = _uploads_dir() / unique_name

    try:
        file.save(save_path)
        _verify_uploaded_image(save_path)

        validation = validate_prescription_document(save_path)
        if not validation.get("success"):
            return jsonify(
                {
                    "success": False,
                    "message": validation.get("error")
                    or "Document validation could not be completed.",
                }
            ), 500

        if not validation.get("is_document"):
            return jsonify(
                {
                    "success": False,
                    "is_document": False,
                    "message": "This image does not look like a prescription.",
                    "reasons": validation.get("reasons") or [],
                    "confidence_score": validation.get("confidence_score", 0.0),
                }
            ), 400

        result = _run_ocr_for_prescription(
            save_path,
            prescription_id,
            image_filename=safe_name,
        )
        return jsonify(result)
    except OCRResultServiceError as exc:
        return jsonify({"success": False, "message": str(exc)}), 500
    except PharmacistServiceError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    finally:
        if save_path.exists():
            save_path.unlink(missing_ok=True)


@pharmacist_bp.route("/api/prescriptions/<prescription_id>/sample-ocr", methods=["POST"])
@login_required
@role_required("pharmacist")
def api_sample_ocr(prescription_id):
    prescription = get_prescription(prescription_id)
    if not prescription:
        return jsonify({"success": False, "message": "Prescription not found."}), 404

    payload = request.get_json(silent=True) or {}
    sample_file = (payload.get("sample_file") or request.form.get("sample_file") or "").strip()

    try:
        result = _process_sample_ocr(prescription_id, sample_file)
        return jsonify(result)
    except OCRResultServiceError as exc:
        return jsonify({"success": False, "message": str(exc)}), 500
    except PharmacistServiceError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@pharmacist_bp.route("/prescriptions/<prescription_id>/sample-ocr", methods=["POST"])
@login_required
@role_required("pharmacist")
def sample_ocr(prescription_id):
    prescription = get_prescription(prescription_id)
    if not prescription:
        flash("Prescription not found.", "danger")
        return redirect(url_for("pharmacist.search"))

    patient_id = prescription.get("patient_id", "")
    sample_file = (request.form.get("sample_file") or "").strip()

    try:
        _process_sample_ocr(prescription_id, sample_file)
        flash(
            f"Sample '{sample_file}' decoded successfully. Review and edit before dispensing.",
            "success",
        )
    except OCRResultServiceError as exc:
        flash(f"OCR succeeded but could not save result: {exc}", "danger")
    except PharmacistServiceError as exc:
        flash(str(exc), "warning" if not sample_file else "danger")

    return redirect(
        url_for(
            "pharmacist.prescriptions",
            patient_id=patient_id,
            rx=prescription_id,
        )
    )


@pharmacist_bp.route("/prescriptions/<prescription_id>/ocr", methods=["GET", "POST"])
@login_required
@role_required("pharmacist")
def ocr_upload(prescription_id):
    prescription = get_prescription(prescription_id)
    if not prescription:
        flash("Prescription not found.", "danger")
        return redirect(url_for("pharmacist.search"))

    patient = get_patient_by_patient_id(prescription.get("patient_id", ""))
    ocr_results = get_ocr_results_for_prescription(prescription_id)
    sample_files = list_sample_prescription_files(_test_prescriptions_dir())

    if request.method == "POST":
        file = request.files.get("image")
        if not file or not file.filename:
            flash("Please select a prescription image to upload.", "danger")
            return redirect(url_for("pharmacist.ocr_upload", prescription_id=prescription_id))

        if not _allowed_file(file.filename):
            flash("Allowed formats: JPG, PNG, WEBP.", "danger")
            return redirect(url_for("pharmacist.ocr_upload", prescription_id=prescription_id))

        safe_name = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{safe_name}"
        save_path = _uploads_dir() / unique_name

        try:
            file.save(save_path)
            _verify_uploaded_image(save_path)
            _run_ocr_for_prescription(
                save_path,
                prescription_id,
                image_filename=safe_name,
            )
            flash("Prescription image decoded and saved successfully.", "success")
            return redirect(
                url_for(
                    "pharmacist.prescriptions",
                    patient_id=prescription.get("patient_id", ""),
                    rx=prescription_id,
                )
            )
        except OCRResultServiceError as exc:
            flash(f"OCR succeeded but could not save result: {exc}", "danger")
        except PharmacistServiceError as exc:
            flash(str(exc), "danger")
        finally:
            if save_path.exists():
                save_path.unlink(missing_ok=True)

    latest_ocr_text = get_latest_ocr_text_for_prescription(prescription_id)

    return render_template(
        "pharmacist/ocr_upload.html",
        prescription=prescription,
        patient=patient,
        ocr_results=ocr_results,
        sample_files=sample_files,
        latest_ocr_text=latest_ocr_text,
    )


@pharmacist_bp.route("/api/side-effects")
@login_required
@role_required("pharmacist")
def api_side_effects():
    medication = request.args.get("medication", "").strip()
    if not medication:
        return jsonify(
            {
                "available": False,
                "message": "Medication name is required.",
                "details": {},
                "clinical_trials": [],
            }
        ), 400

    side_effects = get_medication_side_effects(medication)
    trials = search_clinical_trials(medication, search_type="term")
    side_effects["clinical_trials"] = trials.get("studies", [])[:5]
    if trials.get("error"):
        side_effects["clinical_trials_error"] = trials["error"]

    return jsonify(side_effects)


@pharmacist_bp.route("/consultation/side-effects")
@login_required
@role_required("pharmacist")
def side_effects():
    medication = request.args.get("medication", "").strip()
    result = None
    if medication:
        result = get_medication_side_effects(medication)
    return render_template(
        "pharmacist/side_effects.html",
        medication=medication,
        result=result,
    )


@pharmacist_bp.route("/consultation/clinical-trials")
@login_required
@role_required("pharmacist")
def clinical_trials():
    query = request.args.get("query", "").strip()
    search_type = request.args.get("type", "condition")
    payload = None
    if query:
        payload = search_clinical_trials(query, search_type=search_type)
    return render_template(
        "pharmacist/clinical_trials.html",
        query=query,
        search_type=search_type,
        payload=payload,
    )