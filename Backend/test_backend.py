from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# Test for valid XML
def test_valid_xml_upload():
    with open("Backend/tests/valid_moodle.xml", "rb") as f:
        response = client.post("/upload/", files={"files": ("valid_moodle.xml", f)})
    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
    assert len(data["questions"]) > 0  # Ensure we get questions in response


# Test for invalid XML
def test_invalid_xml_upload():
    with open("Backend/tests/invalid_moodle.xml", "rb") as f:
        response = client.post("/upload/", files={"files": ("invalid_moodle.xml", f)})
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid XML format: not well-formed (invalid token): line 68, column 1"
    }


# Test for export questions
def test_export_questions():
    data = {
        "questions": [
            {
                "type": "multiple_choice",
                "name": "Test",
                "text": "Test.",
                "answers": [
                    {"text": "Answer A", "correct": True},
                    {"text": "Answer B", "correct": False},
                ],
                "subquestions": [],
            }
        ]
    }
    response = client.post("/export/", json=data)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/xml"
    assert (
        response.headers["Content-Disposition"]
        == "attachment; filename=exported_questions.xml"
    )
    assert response.text.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    assert "<quiz>" in response.text
    assert "<question" in response.text


# Test for export with no questions selected
def test_export_no_questions():
    data = {"questions": []}
    response = client.post("/export/", json=data)
    assert response.status_code == 400
    assert response.json() == {"detail": "No questions selected for export."}


# Test for uploading and parsing
def test_upload_and_parse_xml():
    with open("Backend/tests/valid_moodle.xml", "rb") as f:
        response = client.post("/upload/", files={"files": ("sample_moodle.xml", f)})
    
    assert response.status_code == 200
    assert "questions" in response.json()
    questions = response.json()["questions"]
    assert len(questions) > 0
    assert "name" in questions[0]