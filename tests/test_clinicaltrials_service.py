from unittest.mock import patch

from app.services.clinicaltrials_service import search_clinical_trials


@patch("app.services.clinicaltrials_service.requests.get")
def test_search_clinical_trials_parses_response(mock_get):
    mock_get.return_value.json.return_value = {
        "studies": [
            {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT123",
                        "briefTitle": "Diabetes Study",
                    },
                    "statusModule": {"overallStatus": "RECRUITING"},
                    "designModule": {"phases": ["PHASE2"]},
                    "conditionsModule": {"conditions": ["Diabetes"]},
                }
            }
        ]
    }
    mock_get.return_value.raise_for_status.return_value = None

    result = search_clinical_trials("diabetes")
    assert result["studies"][0]["nct_id"] == "NCT123"
    assert result["studies"][0]["title"] == "Diabetes Study"
