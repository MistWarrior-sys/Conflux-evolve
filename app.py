from flask import Flask, request, send_file, render_template_string
from datetime import datetime
import smtplib
from email.message import EmailMessage
import openai
import requests
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

# API Keys
GEMINI_API_KEY = "AIzaSyCiPexCuwjINDw_IGmv_rm1Xfm2sQJtohY"  # ✅ Updated Gemini key
OPENAI_API_KEY = "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"
openai.api_key = OPENAI_API_KEY

# Email
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "abdulrhman.sea@gmail.com"
EMAIL_PASSWORD = "ppmtinvzfoxtycfb"

# PDF path
PDF_FILE = "The_Conflux.pdf"
DASHBOARD_PASSWORD = "Conflux2025!"
DEFAULT_LOOPS = 5
DEFAULT_ARTWORKS = 3
PROJECT_NAME = "The Conflux, 2D video game project"

DASHBOARD_HTML = """
<!doctype html>
<title>The Conflux Automation</title>
<h1>The Conflux Automation Dashboard</h1>
<form method="POST">
    <p>Password: <input type="password" name="password" /></p>
    <p>Loops: <input type="number" name="loops" value="{{ loops }}"></p>
    <p>Artworks: <input type="number" name="artworks" value="{{ artworks }}"></p>
    <p><button name="action" value="trigger">Trigger Manual Run</button></p>
    <p><button name="action" value="reset">Reset to Defaults</button></p>
</form>
"""

@app.route("/", methods=["GET", "POST"])
def dashboard():
    loops = DEFAULT_LOOPS
    artworks = DEFAULT_ARTWORKS
    if request.method == "POST":
        password = request.form.get("password")
        if password != DASHBOARD_PASSWORD:
            return "Incorrect password", 403
        action = request.form.get("action")
        if action == "trigger":
            loops = int(request.form.get("loops", DEFAULT_LOOPS))
            artworks = int(request.form.get("artworks", DEFAULT_ARTWORKS))
            run_brainstorm(loops, artworks)
            return "Manual run triggered!"
        elif action == "reset":
            return render_template_string(DASHBOARD_HTML, loops=DEFAULT_LOOPS, artworks=DEFAULT_ARTWORKS)
    return render_template_string(DASHBOARD_HTML, loops=loops, artworks=artworks)

def generate_reply(prompt, role="chatgpt"):
    if role == "gemini":
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
            params={"key": GEMINI_API_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )
        data = response.json()
        # ✅ Fix: check for 'candidates' or fallback to the new format
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text
        except (KeyError, IndexError):
            return "[Gemini API Error: Unexpected response format]"
    else:
        try:
            # ✅ Fix for openai>=1.0.0 API
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[ChatGPT API Error: {str(e)}]"

def generate_image(prompt):
    try:
        response = openai.images.generate(prompt=prompt, n=1, size="512x512")
        image_url = response["data"][0]["url"]
        img_data = requests.get(image_url).content
        filename = f"/tmp/img_{datetime.now().timestamp()}.png"
        with open(filename, "wb") as f:
            f.write(img_data)
        return filename
    except Exception as e:
        print(f"Image generation failed: {e}")
        return None

def run_brainstorm(loops, artworks):
    doc = SimpleDocTemplate(PDF_FILE, pagesize=A4)
    styles = getSampleStyleSheet()
    content = []
    content.append(Paragraph(f"<b>{PROJECT_NAME} - Brainstorm Session</b>", styles["Title"]))
    content.append(Spacer(1, 12))

    prompt = "Start your brainstorming session between Gemini and ChatGPT about The Conflux, 2D video game project. Please consider the previous brainstorming sessions and start from where you ended the last session."
    for i in range(loops):
        gemini_reply = generate_reply(prompt, "gemini")
        content.append(Paragraph(f"<b>Gemini:</b> {gemini_reply}", styles["Normal"]))
        content.append(Spacer(1, 12))
        chatgpt_reply = generate_reply(gemini_reply, "chatgpt")
        content.append(Paragraph(f"<b>ChatGPT:</b> {chatgpt_reply}", styles["Normal"]))
        content.append(Spacer(1, 12))
        prompt = chatgpt_reply

    for i in range(artworks):
        img_prompt = f"Concept art for The Conflux, 2D cyberpunk side-scroller game - Artwork {i+1}"
        image_path = generate_image(img_prompt)
        if image_path:
            content.append(Spacer(1, 24))
            content.append(Paragraph(f"<b>Artwork {i+1}</b>: {img_prompt}", styles["Heading3"]))
            content.append(Image(image_path, width=300, height=300))
            content.append(Spacer(1, 12))
        else:
            content.append(Paragraph(f"<b>Artwork {i+1}</b>: [Image generation failed]", styles["Normal"]))
            content.append(Spacer(1, 12))

    doc.build(content)
    send_email(PDF_FILE)

def send_email(pdf_file):
    msg = EmailMessage()
    msg["Subject"] = "The Conflux Brainstorm PDF"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = "abdulrhman.sea@gmail.com"
    msg.set_content("Your latest brainstorm PDF is attached.")
    with open(pdf_file, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=pdf_file)
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
    print("Email sent!")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
