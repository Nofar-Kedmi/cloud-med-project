from unittest.mock import MagicMock, patch

from app.services.prescription_service import attach_pdf_to_prescription


@patch("app.services.prescription_service.Prescription.attach_drive_file")
def test_attach_pdf_to_prescription(mock_attach):
    mock_rx = MagicMock(prescription_id="RX-2026-0001")
    mock_attach.return_value = mock_rx

    result = attach_pdf_to_prescription(
        "RX-2026-0001",
        drive_file_url="https://drive.google.com/file/d/abc/view",
        drive_file_id="abc",
    )

    assert result is mock_rx
    mock_attach.assert_called_once_with(
        "RX-2026-0001",
        drive_file_id="abc",
        drive_file_url="https://drive.google.com/file/d/abc/view",
    )
