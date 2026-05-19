from groq import Groq
# ============================================================
# STANDARD IMPORTS
# ============================================================
import os
import io
import traceback

# ============================================================
# THIRD-PARTY IMPORTS
# ============================================================
import requests
from dotenv import load_dotenv

# ---- Flask ----
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
)

# ---- Flask extensions ----
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

# ---- PyTorch ----
import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image

# ---- Google Generative AI (Gemini) ----
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai not installed — Gemini guidance disabled.")


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================
load_dotenv()

GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")
GOOGLE_API_KEY  = os.getenv("GOOGLE_API_KEY", "")


# ============================================================
# FLASK APPLICATION
# ============================================================
app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates",
)

app.secret_key = os.getenv("SECRET_KEY", "skinguard-secret-change-in-prod")


# ============================================================
# DATABASE CONFIGURATION
# ============================================================
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
login_manager.login_view = "login"            # redirect to /login if unauthenticated
login_manager.login_message_category = "info"


# ============================================================
# USER MODEL
# ============================================================
class User(UserMixin, db.Model):
    """Minimal user model — id, username, hashed password."""

    __tablename__ = "users"

    id       = db.Column(db.Integer,     primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))


# ============================================================
# GEMINI SETUP
# ============================================================
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
model="llama-3.3-70b-versatile",
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
grok_client = None
if GROQ_API_KEY:
    try:
        grok_client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq AI configured")
    except Exception as exc:
        print(f"⚠️  Groq configuration failed: {exc}")
# ============================================================
# PYTORCH MODEL SETUP
# ============================================================

# -- Class definitions --
CLASS_NAMES = [
    "Nevus",                  # 0
    "Basal Cell Carcinoma",   # 1
    "Benign Keratosis",       # 2
    "Vascular Lesion",        # 3
    "Melanoma",               # 4
]

CANCER_CLASSES = {"Melanoma", "Basal Cell Carcinoma"}

SEVERITY_MAP = {
    "Melanoma":               "Critical",
    "Basal Cell Carcinoma":   "High",
    "Benign Keratosis":       "Moderate",
    "Nevus":                  "Low",
    "Vascular Lesion":        "Low",
}

# -- Model path --
MODEL_PATH = r"D:\Cancer_detection\best_skin_model.pt"

# -- Image transforms (ImageNet normalisation) --
TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])

# -- Load model --
skin_model = None

def load_skin_model():
    global skin_model
    if skin_model is None:
        skin_model = torch.load(
            "best_skin_model.pt",
            map_location=torch.device("cpu")
        )
    return skin_model
# ============================================================
# HELPER — IMAGE PREPROCESSING
# ============================================================
def preprocess_image(image: Image.Image) -> torch.Tensor:
    """Convert a PIL image to a normalised (1, 3, 224, 224) tensor."""
    image = image.convert("RGB")
    tensor = TRANSFORM(image)
    return tensor.unsqueeze(0)          # add batch dimension


# ============================================================
# HELPER — GEMINI AI GUIDANCE
# ============================================================
def get_ai_guidance(prediction: str, confidence: float, cancer_status: str) -> str:
    fallback = (
        f"Prediction: {prediction} ({cancer_status}). "
        f"Confidence: {confidence:.1f}%. Please consult a dermatologist."
    )
    if grok_client is None:
        return fallback
    try:
        response = grok_client.chat.completions.create(
            model="grok-3-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional medical AI assistant specialising in dermatology."
                },
                {
                    "role": "user",
                    "content": f"""A skin lesion analysis produced:
- Predicted condition: {prediction}
- Cancer status: {cancer_status}
- Confidence: {confidence:.1f}%

Provide:
1. Disease Overview
2. Severity Assessment
3. Immediate Recommendations
4. 5 Self-Care Steps
5. Warning Signs
6. Doctor Visit Advice

Remind user this is an AI tool, not a diagnosis."""
                }
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        print(f"⚠️  Grok guidance error: {exc}")
        return fallback
# ============================================================
# ROUTE — HOME
# ============================================================
@app.route("/")
def home():
    return render_template("index.html")
@app.route("/learn")
def leern():
    return render_template("learn.html")

# ============================================================
# ROUTE — SIGNUP
# ============================================================
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return render_template(
                "signup.html",
                error="Username and password are required.",
            )

        if User.query.filter_by(username=username).first():
            return render_template(
                "signup.html",
                error="Username already taken. Please choose another.",
            )

        try:
            hashed_pw = generate_password_hash(password)
            new_user  = User(username=username, password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("login"))

        except Exception as exc:
            db.session.rollback()
            traceback.print_exc()
            return render_template(
                "signup.html",
                error=f"Database error: {exc}",
            )

    return render_template("signup.html", error=None)


# ============================================================
# ROUTE — LOGIN
# ============================================================
@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("home"))

        return render_template(
            "login.html",
            error="Invalid username or password.",
        )

    return render_template("login.html", error=None)


# ============================================================
# ROUTE — LOGOUT
# ============================================================
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))
# ============================================================
# ROUTE — LEARN PAGE
# ============================================================
@app.route('/learn')
def learn():
    return render_template('learn.html')


# ============================================================
# ROUTE — CHAT API (Gemini)
# ============================================================
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data    = request.get_json(silent=True) or {}
        message = data.get('message', '').strip()

        if not message:
            return jsonify({'reply': 'Please ask a question.'})

        if grok_client is None:
            return jsonify({'reply': 'AI assistant unavailable. Check XAI_API_KEY in .env'})

        response = grok_client.chat.completions.create(
            model="grok-3-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful skin health assistant. Answer questions about skin cancer and dermatology clearly in 2-4 sentences. Always recommend consulting a real dermatologist."
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
        )
        reply = response.choices[0].message.content.strip()
        return jsonify({'reply': reply})

    except Exception as exc:
        traceback.print_exc()
        return jsonify({'reply': f'Error: {str(exc)}'})
# ============================================================
# ROUTE — DERMOSCAN PAGE
# ============================================================
@app.route("/dermoscan")
@login_required
def dermoscan():
    return render_template("dermoscan.html")


# ============================================================
# ROUTE — ANALYZE API  (POST /dermoscan/api/analyze)
# ============================================================
@app.route("/dermoscan/api/analyze", methods=["POST"])
@login_required
def analyze():
    """
    Accepts a multipart image upload, runs inference, returns JSON.
    """

    try:

        # -- 1. Check model --
        if skin_model is None:
            return jsonify({
                "ok":    False,
                "error": "Model not loaded. Contact the administrator.",
            }), 503

        # -- 2. Validate upload --
        if "file" not in request.files:
            return jsonify({"ok": False, "error": "No image file provided."}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"ok": False, "error": "Empty filename."}), 400

        # -- 3. Open image --
        try:
            image = Image.open(io.BytesIO(file.read())).convert("RGB")
        except Exception:
            return jsonify({"ok": False, "error": "Cannot read image file."}), 400

        # -- 4. Preprocess --
        tensor = preprocess_image(image)

        # -- 5. Inference --
        with torch.no_grad():
            outputs = skin_model(tensor)
            probs   = F.softmax(outputs, dim=1)[0]

        confidence_val, predicted_idx = torch.max(probs, 0)
        predicted_class    = CLASS_NAMES[predicted_idx.item()]
        confidence_percent = round(confidence_val.item() * 100, 2)

        # -- 6. Probability distribution --
        distribution = {
            CLASS_NAMES[i]: round(p.item() * 100, 2)
            for i, p in enumerate(probs)
        }

        # -- 7. Derived metadata --
        is_cancer     = predicted_class in CANCER_CLASSES
        cancer_status = "Cancerous" if is_cancer else "Non-Cancerous"
        severity      = SEVERITY_MAP.get(predicted_class, "Low")

        # -- 8. Gemini guidance --
        guidance = get_ai_guidance(
            prediction=predicted_class,
            confidence=confidence_percent,
            cancer_status=cancer_status,
        )

        return jsonify({
            "ok":            True,
            "prediction":    predicted_class,
            "confidence":    confidence_percent,
            "distribution":  distribution,
            "is_cancer":     is_cancer,
            "cancer_status": cancer_status,
            "severity":      severity,
            "guidance":      guidance,
        })

    except Exception as exc:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(exc)}), 500


# ============================================================
# ROUTE — HOSPITALS PAGE
# ============================================================
@app.route("/hospitals")
@login_required
def hospitals():
    return render_template("hospitals.html")


# ============================================================
# ROUTE — SEARCH HOSPITALS API  (POST /search_hospitals)
# ============================================================
@app.route("/search_hospitals", methods=["POST"])
@login_required
def search_hospitals():
    """
    Accepts JSON  { "location": "<address or city>" }
    Uses Google Geocoding + Places Nearby Search.
    Returns JSON  { "center": {lat, lng}, "hospitals": [...] }
    """

    try:

        data     = request.get_json(silent=True) or {}
        location = data.get("location", "").strip()

        if not location:
            return jsonify({"ok": False, "error": "Location is required."}), 400

        if not GOOGLE_API_KEY:
            return jsonify({
                "ok":       False,
                "error":    "Google API key not configured.",
                "center":   {},
                "hospitals": [],
            }), 503

        # -- Geocoding --
        geo_url = (
            "https://maps.googleapis.com/maps/api/geocode/json"
            f"?address={requests.utils.quote(location)}"
            f"&key={GOOGLE_API_KEY}"
        )

        geo_res = requests.get(geo_url, timeout=10).json()

        if not geo_res.get("results"):
            return jsonify({
                "ok":       False,
                "error":    "Location not found.",
                "center":   {},
                "hospitals": [],
            })

        geo_location = geo_res["results"][0]["geometry"]["location"]
        lat = geo_location["lat"]
        lng = geo_location["lng"]

        # -- Nearby hospital search --
        nearby_url = (
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            f"?location={lat},{lng}"
            "&radius=5000"
            "&type=hospital"
            f"&key={GOOGLE_API_KEY}"
        )

        nearby_res = requests.get(nearby_url, timeout=10).json()

        hospitals_list = []
        for place in nearby_res.get("results", []):
            hospitals_list.append({
                "name":     place.get("name", "Unknown Hospital"),
                "address":  place.get("vicinity", "Address not available"),
                "rating":   place.get("rating", "N/A"),
                "open_now": place.get("opening_hours", {}).get("open_now", False),
                "lat":      place["geometry"]["location"]["lat"],
                "lng":      place["geometry"]["location"]["lng"],
            })

        return jsonify({
            "ok":       True,
            "center":   {"lat": lat, "lng": lng},
            "hospitals": hospitals_list,
        })

    except requests.exceptions.Timeout:
        return jsonify({"ok": False, "error": "Request to Google API timed out."}), 504

    except Exception as exc:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(exc)}), 500


# ============================================================
# ROUTE — HEALTH CHECK
# ============================================================
@app.route("/health")
def health():
    return jsonify({
        "status":       "running",
        "model_loaded": skin_model is not None,
        "gemini_ready": gemini_model is not None,
        "logged_in":    current_user.is_authenticated,
    })


# ============================================================
# DATABASE INITIALISATION
# ============================================================
with app.app_context():
    db.create_all()
    print("✅ Database tables created / verified")


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    print("🚀 SkinGuard AI running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
