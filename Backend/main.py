from typing import List
import io
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException

app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def parse_moodle_xml(file):
    try:
        file_content = file.read().decode("utf-8")
        tree = ET.parse(io.StringIO(file_content))
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid XML format: {e}")

    if root.tag != "quiz":
        raise HTTPException(
            status_code=400, detail="Invalid Moodle XML format: Root tag must be <quiz>"
        )

    questions = []

    for question in root.findall("question"):
        question_type = question.get("type", "unknown")
        question_name = question.find("./name/text")
        question_text = question.find("./questiontext/text")

        parsed_question = {
            "type": question_type,
            "name": (
                question_name.text.strip()
                if question_name is not None
                else "Unnamed Question"
            ),
            "text": (
                filter_html_tags(question_text.text.strip())
                if question_text is not None
                else ""
            ),
            "subquestions": [],
            "answers": [],
        }

        if question_type == "matching":
            for subquestion in question.findall("./subquestion"):
                subquestion_text = subquestion.find("text")
                answer_text = subquestion.find("answer/text")

                subquestion_content = (
                    filter_html_tags(subquestion_text.text.strip())
                    if subquestion_text is not None
                    else ""
                )
                answer_content = (
                    filter_html_tags(answer_text.text.strip())
                    if answer_text is not None
                    else ""
                )
                parsed_question["subquestions"].append(
                    {
                        "subquestion_text": subquestion_content,
                        "answer_text": answer_content,
                    }
                )

        for answer in question.findall("./answer"):
            ans_text = answer.find("text")
            is_correct = answer.get("fraction") == "100"
            if ans_text is not None:
                parsed_question["answers"].append(
                    {
                        "text": filter_html_tags(ans_text.text.strip()),
                        "correct": is_correct,
                    }
                )
        questions.append(parsed_question)
    return questions


def filter_html_tags(answers):
    soup = BeautifulSoup(answers, "html.parser")
    text = soup.get_text(separator=" ").strip()
    return text


@app.post("/upload/")
async def upload_files(files: List[UploadFile] = File(...)):
    all_questions = []

    for file in files:
        print(f"Received file: {file.filename}")
        questions = parse_moodle_xml(file.file)
        all_questions.extend(questions)
    return {"questions": all_questions}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8080)
