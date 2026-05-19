from groq import Groq
import os
import io
import traceback
import requests

from dotenv import load_dotenv

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
)

from flask_sqlalchemy import SQLAlchemy

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)

from werkzeug.security import generate_password_hash, check_password_hash

import torch
import torch.nn.functional as F

from torchvision import transforms
from torchvision.models import resnet18

from PIL import Image


# ============================================================
# ENV
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "secret123")


# ============================================================
# APP
# ============================================================

app = Flask(__name__)

app.secret_key = SECRET_KEY

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + os.path.join(BASE_DIR, "users.db")
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ============================================================
# LOGIN MANAGER
# ============================================================

login_manager = LoginManager()

login_manager.init_app(app)

login_manager.login_view = "login"


# ============================================================
# USER MODEL
# ============================================================

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(300), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ============================================================
# GROQ
# ============================================================

grok_client = None

if GROQ_API_KEY:

    try:

        grok_client = Groq(api_key=GROQ_API_KEY)

        print("✅ Groq AI Ready")

    except Exception as e:

        print("Groq Error:", e)


# ============================================================
# MODEL CONFIG
# ============================================================

CLASS_NAMES = [
    "Nevus",
    "Basal Cell Carcinoma",
    "Benign Keratosis",
    "Vascular Lesion",
    "Melanoma"
]

CANCER_CLASSES = {
    "Melanoma",
    "Basal Cell Carcinoma"
}

SEVERITY_MAP = {
    "Melanoma": "Critical",
    "Basal Cell Carcinoma": "High",
    "Benign Keratosis": "Moderate",
    "Nevus": "Low",
    "Vascular Lesion": "Low",
}

MODEL_PATH = os.path.join(BASE_DIR, "best_skin_model.pt")


# ============================================================
# TRANSFORMS
# ============================================================

TRANSFORM = transforms.Compose([

    transforms.Resize((224, 224)),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# ============================================================
# LOAD MODEL
# ============================================================



# ============================================================
# AI GUIDANCE
# ============================================================

def get_ai_guidance(prediction, confidence, cancer_status):

    fallback = (
        f"{prediction} detected with "
        f"{confidence}% confidence."
    )

    if grok_client is None:
        return fallback

    try:

        response = grok_client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[

                {
                    "role": "system",
                    "content": "You are a dermatology AI assistant."
                },

                {
                    "role": "user",
                    "content": f"""
Predicted disease: {prediction}
Cancer status: {cancer_status}
Confidence: {confidence}%

Give:
1. Overview
2. Severity
3. Care tips
4. Warning signs
5. Doctor advice
"""
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:

        print("AI ERROR:", e)

        return fallback


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form.get("username")

        password = request.form.get("password")

        existing = User.query.filter_by(username=username).first()

        if existing:

            return render_template(
                "signup.html",
                error="Username already exists"
            )

        hashed = generate_password_hash(password)

        user = User(
            username=username,
            password=hashed
        )

        db.session.add(user)

        db.session.commit()

        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")

        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            login_user(user)

            return redirect(url_for("home"))

        return render_template(
            "login.html",
            error="Invalid credentials"
        )

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("home"))


@app.route("/learn")
def learn():
    return render_template("learn.html")


@app.route("/hospitals")
@login_required
def hospitals():
    return render_template("hospitals.html")


@app.route("/dermoscan")
@login_required
def dermoscan():
    return render_template("dermoscan.html")


# ============================================================
# ANALYZE API
# ============================================================

@app.route("/dermoscan/api/analyze", methods=["POST"])
@login_required
def analyze():

    try:

        if skin_model is None:

            return jsonify({
                "ok": False,
                "error": "Model not loaded"
            })

        if "file" not in request.files:

            return jsonify({
                "ok": False,
                "error": "No image uploaded"
            })

        file = request.files["file"]

        image = Image.open(file).convert("RGB")

        tensor = TRANSFORM(image).unsqueeze(0)

        with torch.no_grad():

            outputs = skin_model(tensor)

            probs = F.softmax(outputs, dim=1)[0]

        confidence, predicted = torch.max(probs, 0)

        prediction = CLASS_NAMES[predicted.item()]

        confidence_percent = round(
            confidence.item() * 100,
            2
        )

        cancer_status = (
            "Cancerous"
            if prediction in CANCER_CLASSES
            else "Non-Cancerous"
        )

        guidance = get_ai_guidance(
            prediction,
            confidence_percent,
            cancer_status
        )

        distribution = {

            CLASS_NAMES[i]: round(
                probs[i].item() * 100,
                2
            )

            for i in range(len(CLASS_NAMES))
        }

        return jsonify({

            "ok": True,

            "prediction": prediction,

            "confidence": confidence_percent,

            "distribution": distribution,

            "cancer_status": cancer_status,

            "severity": SEVERITY_MAP[prediction],

            "guidance": guidance
        })

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "ok": False,
            "error": str(e)
        })


# ============================================================
# HOSPITAL SEARCH
# ============================================================

@app.route("/search_hospitals", methods=["POST"])
@login_required
def search_hospitals():

    try:

        data = request.get_json()

        location = data.get("location")

        geo_url = (
            "https://maps.googleapis.com/maps/api/geocode/json"
            f"?address={location}"
            f"&key={GOOGLE_API_KEY}"
        )

        geo_res = requests.get(geo_url).json()

        if not geo_res["results"]:

            return jsonify({
                "hospitals": []
            })

        lat = geo_res["results"][0]["geometry"]["location"]["lat"]

        lng = geo_res["results"][0]["geometry"]["location"]["lng"]

        nearby_url = (
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            f"?location={lat},{lng}"
            "&radius=5000"
            "&type=hospital"
            f"&key={GOOGLE_API_KEY}"
        )

        nearby_res = requests.get(nearby_url).json()

        hospitals = []

        for place in nearby_res.get("results", []):

            hospitals.append({

                "name": place.get("name"),

                "address": place.get("vicinity"),

                "rating": place.get("rating"),

                "open_now": place.get(
                    "opening_hours",
                    {}
                ).get("open_now", False),

                "lat": place["geometry"]["location"]["lat"],

                "lng": place["geometry"]["location"]["lng"]
            })

        return jsonify({

            "center": {
                "lat": lat,
                "lng": lng
            },

            "hospitals": hospitals
        })

    except Exception as e:

        traceback.print_exc()

        return jsonify({
            "error": str(e)
        })


# ============================================================
# HEALTH
# ============================================================

@app.route("/health")
def health():

    return jsonify({

        "status": "running",

        "model_loaded": skin_model is not None,

        "logged_in": current_user.is_authenticated
    })


# ============================================================
# DB INIT
# ============================================================

with app.app_context():

    db.create_all()

    print("✅ Database Ready")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
