import os

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from flask_login import current_user, login_required



from app.middleware.rbac import role_required

from app.models.patient import Patient

from app.models.prescription import Prescription

from app.models.visit import Visit

from app.services.patient_service import PatientNotFoundError, get_patient

from app.services.pdf_service import generate_prescription_pdf

from app.services.prescription_service import attach_pdf_to_prescription, get_prescription_for_visit

from app.services.search_service import search_medical_info

from app.services.storage_service import StorageServiceError, upload_pdf_to_drive

from app.services.visit_service import ClinicalEncounterError, get_recent_visits_for_dashboard, save_visit_and_prescription



doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")





@doctor_bp.route("/dashboard")

@login_required

@role_required("doctor")

def dashboard():

    doctor_id = current_user.get_id()

    recent_visits = get_recent_visits_for_dashboard(doctor_id, limit=5)

    visit_count = Visit.count_by_doctor(doctor_id)

    prescription_count = Prescription._collection().count_documents({"doctor_id": doctor_id})

    return render_template(

        "doctor/dashboard.html",

        recent_visits=recent_visits,

        visit_count=visit_count,

        prescription_count=prescription_count,

    )





@doctor_bp.route("/search")

@login_required

@role_required("doctor")

def search():

    query = request.args.get("query", request.args.get("q", "")).strip()

    patients = Patient.search(query) if query else []

    return render_template("doctor/patient_search.html", query=query, patients=patients)





@doctor_bp.route("/visit/new")

@login_required

@role_required("doctor")

def create_new_visit():

    patients = Patient.find_all_sorted()

    return render_template("doctor/new_visit.html", patients=patients)





@doctor_bp.route("/visit/new/<patient_id>", methods=["GET"])

@login_required

@role_required("doctor")

def visit_new(patient_id):

    try:

        patient = get_patient(patient_id)

    except PatientNotFoundError:

        flash("Patient not found.", "danger")

        return redirect(url_for("doctor.create_new_visit"))



    from datetime import date



    return render_template(

        "doctor/visit_form.html",

        patient=patient,

        today=date.today().isoformat(),

        form={},

    )





@doctor_bp.route("/visit/details/<visit_id>")

@login_required

@role_required("doctor")

def visit_details(visit_id):

    visit = Visit.find_by_visit_id(visit_id)

    if not visit:

        flash("Visit record not found.", "danger")

        return redirect(url_for("doctor.dashboard"))



    patient = Patient.find_by_patient_id(visit.patient_id)

    prescription = get_prescription_for_visit(visit.visit_id)



    return render_template(

        "doctor/visit_details.html",

        visit=visit,

        patient=patient,

        prescription=prescription,

    )





@doctor_bp.route("/visit/save", methods=["POST"])

@login_required

@role_required("doctor")

def visit_save():

    patient_id = (request.form.get("patient_id") or "").strip().upper()

    try:

        patient = get_patient(patient_id)

    except PatientNotFoundError:

        flash("Patient not found.", "danger")

        return redirect(url_for("doctor.create_new_visit"))



    pdf_filepath = None

    try:

        visit, prescription = save_visit_and_prescription(

            current_user.get_id(),

            request.form.to_dict(),

        )



        pdf_filepath, _pdf_filename = generate_prescription_pdf(

            visit,

            prescription,

            patient,

            doctor_name=current_user.full_name,

            doctor_license_number=os.environ.get("DOCTOR_LICENSE_NUMBER", ""),

        )



        try:

            upload_result = upload_pdf_to_drive(pdf_filepath, drive_filename=_pdf_filename)

            attach_pdf_to_prescription(

                prescription.prescription_id,

                drive_file_url=upload_result["web_view_link"],

                drive_file_id=upload_result["file_id"],

            )

            flash(

                f"Visit {visit.visit_id} saved and prescription PDF uploaded to Google Drive.",

                "success",

            )

        except StorageServiceError as exc:

            flash(

                f"Visit {visit.visit_id} saved, but PDF upload failed: {exc}",

                "warning",

            )

        except Exception as exc:

            flash(

                f"Visit {visit.visit_id} saved, but PDF upload failed: {exc}",

                "warning",

            )



        return redirect(url_for("doctor.visit_details", visit_id=visit.visit_id))



    except ClinicalEncounterError as exc:

        for error in exc.errors:

            flash(error, "danger")

    finally:

        if pdf_filepath and os.path.exists(pdf_filepath):

            os.remove(pdf_filepath)



    from datetime import date



    return render_template(

        "doctor/visit_form.html",

        patient=patient,

        today=date.today().isoformat(),

        form=request.form,

    )





@doctor_bp.route("/api/research")

@login_required

@role_required("doctor")

def medical_research():

    diagnosis = request.args.get("diagnosis", "").strip()

    if not diagnosis:

        return jsonify(

            {

                "available": False,

                "message": "Enter a diagnosis before searching.",

                "results": [],

            }

        )



    payload = search_medical_info(f"{diagnosis} clinical guidelines medical research")

    if payload.get("error"):

        return jsonify(

            {

                "available": False,

                "message": payload["error"],

                "results": [],

            }

        )



    results = [

        {

            "title": item.get("title", "Untitled"),

            "url": item.get("url", ""),

            "content": item.get("content", ""),

            "reliability_score": item.get("reliability_score"),

        }

        for item in payload.get("results", [])[:3]

    ]



    return jsonify(

        {

            "available": True,

            "message": "Recent medical articles and clinical guidelines.",

            "results": results,

        }

    )


