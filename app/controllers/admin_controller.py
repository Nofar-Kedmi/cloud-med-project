from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, logout_user

from app.middleware.rbac import role_required
from app.services import auth_service
from app.services.patient_service import (
    PatientNotFoundError,
    PatientValidationError,
    create_patient,
    get_patient,
    list_patients,
    update_patient,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/patients")
@login_required
@role_required("admin")
def patients_list():
    page = request.args.get("page", 1, type=int)
    result = list_patients(page=page)
    return render_template("admin/patients_list.html", **result)


@admin_bp.route("/patients/new", methods=["GET", "POST"])
@login_required
@role_required("admin")
def patient_new():
    if request.method == "POST":
        try:
            patient = create_patient(request.form.to_dict())
            flash(f"Patient {patient.patient_id} created successfully.", "success")
            return redirect(url_for("admin.patients_list"))
        except PatientValidationError as exc:
            for error in exc.errors:
                flash(error, "danger")
            return render_template("admin/patient_form.html", patient=None, form=request.form)

    return render_template("admin/patient_form.html", patient=None, form={})


@admin_bp.route("/patients/<patient_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def patient_edit(patient_id):
    try:
        patient = get_patient(patient_id)
    except PatientNotFoundError:
        flash("Patient not found.", "danger")
        return redirect(url_for("admin.patients_list"))

    if request.method == "POST":
        try:
            update_patient(patient_id, request.form.to_dict())
            flash(f"Patient {patient_id} updated successfully.", "success")
            return redirect(url_for("admin.patients_list"))
        except PatientValidationError as exc:
            for error in exc.errors:
                flash(error, "danger")
            return render_template("admin/patient_form.html", patient=patient, form=request.form)

    return render_template("admin/patient_form.html", patient=patient, form={})
