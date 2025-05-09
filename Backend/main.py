from typing import List
import io
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Response, UploadFile, File, HTTPException
from xml.dom import minidom
import base64

app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def parse_moodle_xml(file, seen_questions):
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
        question_name_element = question.find("./name/text")

        if question_name_element is None or not question_name_element.text.strip():
            continue

        question_name = question_name_element.text.strip()

        if (question_name, question_type) in seen_questions:
            continue  # skip already existing questions

        seen_questions.add((question_name, question_type))

        question_text_element = question.find("./questiontext/text")

        parsed_question = {
            "type": question_type,
            "name": question_name,
            "text": (
                filter_html_tags(question_text_element.text.strip())
                if question_text_element is not None
                else ""
            ),
            "subquestions": [],
            "answers": [],
            "images": [],
        }

        for file_tag in question.findall(".//file"):
            encoding = file_tag.get("encoding")
            if encoding == "base64":
                image_data = base64.b64decode(file_tag.text.strip())
                image_base64 = base64.b64encode(image_data).decode("utf-8")
                parsed_question["images"].append(f"data:image/png;base64, {image_base64}")
                
        # questions need to be selected
        if question_type == "matching":
            for subquestion in question.findall("./subquestion"):
                subquestion_text = subquestion.find("text")
                answer_text = subquestion.find("answer/text")

                subquestion_content = (
                    filter_html_tags(subquestion_text.text.strip())
                    if subquestion_text is not None and subquestion_text.text is not None
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
                        "selected": False,
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
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    all_questions = []
    seen_questions = set()  # Set for duplicate questions

    for file in files:
        print(f"Received file: {file.filename}")
        questions = parse_moodle_xml(file.file, seen_questions)
        all_questions.extend(questions)

    return {"questions": all_questions}


@app.post("/export/")
async def export_questions(data: dict):
    questions = data.get("questions", [])

    if not questions:
        raise HTTPException(status_code=400, detail="No questions selected for export.")

    root = ET.Element("quiz")

    for q in questions:
        question_el = ET.SubElement(root, "question", type=q["type"])
        name_el = ET.SubElement(question_el, "name")
        ET.SubElement(name_el, "text").text = q["name"]

        text_el = ET.SubElement(question_el, "questiontext", format="html")
        question_text = ET.SubElement(text_el, "text")

        # PLUGINFILE for moodle
        image_tags = ""
        for i in range(len(q.get("images", []))):
            image_tags += f'<img src="@@PLUGINFILE@@/image{i}.png" /><br/>'

        html_content = image_tags + q["text"]

        question_text.text = f"<![CDATA[{html_content}]]>"
        question_text.text = html_content

        # file tag for moodle
        for i, base64_img in enumerate(q.get("images", [])):
            image_data = base64_img.split(",")[1].strip()
            file_el = ET.SubElement(text_el, "file", name=f"image{i}.png", encoding="base64", path="/")
            file_el.text = image_data

        # matching type for question
        if q["type"] == "matching":
            for subq in q.get("subquestions", []):
                sub_el = ET.SubElement(question_el, "subquestion")
                sub_q_text = ET.SubElement(sub_el, "text")
                sub_q_text.text = subq["subquestion_text"]
                sub_ans = ET.SubElement(sub_el, "answer")
                ET.SubElement(sub_ans, "text").text = subq["answer_text"]

        # normal answers (multichoice, etc...)
        for answer in q.get("answers", []):
            answer_el = ET.SubElement(
                question_el, "answer", fraction="100" if answer["correct"] else "0"
            )
            ET.SubElement(answer_el, "text").text = answer["text"]

    xml_data = ET.tostring(root, encoding="utf-8", method="xml")

    # pretty_xml for exported xml formatting
    pretty_xml = minidom.parseString(xml_data).toprettyxml(indent="  ")
    lines = pretty_xml.splitlines()
    filtered_lines = [line for line in lines if not line.strip().startswith("<?xml")]
    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + "\n".join(filtered_lines)

    return Response(
        content=xml_str,
        media_type="application/xml",
        headers={"Content-Disposition": "attachment; filename=exported_questions.xml"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8080)
