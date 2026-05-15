# SkinGuard AI — Intelligent Skin Cancer Detection & Healthcare Assistance Platform

## Overview

SkinGuard AI is an AI-powered healthcare platform designed to assist in the early detection of skin cancer using deep learning and intelligent healthcare integrations. The system analyzes uploaded skin lesion images, predicts possible skin conditions, classifies cancerous vs non-cancerous cases, generates AI-powered medical guidance using Gemini AI, and helps users locate nearby hospitals in real time.

---

# Features

* AI-based skin lesion classification
* Cancer / Non-cancer prediction
* Confidence score generation
* PyTorch ResNet18 deep learning model
* Gemini AI personalized recommendations
* Nearby hospital finder using Google Maps APIs
* User authentication system
* Modern responsive dashboard UI
* Real-time image analysis workflow
* Secure Flask backend

---

# Supported Disease Classes

* Melanoma
* Basal Cell Carcinoma (BCC)
* Benign Keratosis
* Vascular Lesion
* Nevus

---

# Tech Stack

## Frontend

* HTML
* CSS
* JavaScript

## Backend

* Flask
* Flask-Login
* Flask-SQLAlchemy

## AI / Deep Learning

* PyTorch
* Torchvision
* ResNet18
* Pillow
* NumPy

## APIs

* Gemini 1.5 Flash API
* Google Geocoding API
* Google Places API

## Database

* SQLite

---

# Project Workflow

1. User uploads skin lesion image
2. Image preprocessing using Torchvision transforms
3. Deep learning model performs inference
4. Softmax probabilities are generated
5. Cancer detection logic is applied
6. Gemini AI generates personalized guidance
7. Nearby hospitals are fetched using Google APIs
8. Results are displayed on the dashboard

---

# Deep Learning Model

* Architecture: ResNet18
* Framework: PyTorch
* Input Size: 224x224
* Transfer Learning: Pretrained weights
* Optimizer: Adam
* Loss Function: CrossEntropyLoss
* Validation Strategy: Stratified train-validation split
* Early Stopping enabled

---

# Installation

## Clone Repository

```bash
git clone https://github.com/yourusername/SkinGuardAI.git
cd SkinGuardAI
```

## Create Virtual Environment

```bash
python -m venv venv
```

## Activate Environment

### Windows PowerShell

```bash
.\venv\Scripts\Activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file:

```env
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

---

# Run Project

```bash
python app.py
```

Application runs on:

```txt
http://localhost:5000
```

---

# Folder Structure

```txt
SkinGuardAI/
│
├── app/
│   ├── app.py
│   ├── templates/
│   ├── static/
│   ├── users.db
│   └── .env
│
├── model/
│   └── best_model.pth
│
├── requirements.txt
└── README.md
```

---

# Hospital Finder

The platform integrates:
* Google Geocoding API
* Google Places API
Features:
* Nearby hospital search
* Ratings
* Address details
* Real-time map support

---

# Gemini AI Integration

Gemini AI dynamically generates:
* Personalized healthcare suggestions
* Warning signs
* Severity explanations
* Medical recommendations
* Preventive care steps

---

# Future Enhancements
* Mobile application
* Grad-CAM heatmaps
* Doctor appointment booking
* Medical report generation
* Multilingual support
* AI chatbot assistant
* Cloud GPU deployment

---

# Challenges Faced
* PyTorch model integration
* API dependency conflicts
* Gemini API integration
* Frontend responsiveness
* Hospital API handling
* Deployment optimization

---
# Deployment
platform:
* Render
* 
Deployment includes:
* requirements.txt
* environment variables
* Flask production server
* GitHub integration

---
# Impact
SkinGuard AI aims to:
* Improve early cancer detection
* Increase healthcare accessibility
* Reduce diagnosis delays
* Assist users with AI-powered healthcare guidance
* Support intelligent healthcare systems

---
# License
This project is developed for educational, research, hackathon, and healthcare innovation purposes.
---
# Author
Developed as an AI-powered healthcare innovation project using Flask, PyTorch, Gemini AI, and Google APIs.
