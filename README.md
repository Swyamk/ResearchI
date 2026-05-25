# 🥗 NutriMind – Personalized Multimodal Nutrition Intelligence System

[![CI/CD](https://github.com/Swyamk/ResearchI/actions/workflows/ci.yml/badge.svg)](https://github.com/Swyamk/ResearchI/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

> AI-powered nutrition intelligence platform with multimodal food analysis, personalized recommendations, and Gemini AI coaching.

---

## 🏗️ Architecture Overview

```
NutriMind/
├── 📱 mobile/          Flutter mobile app (iOS + Android)
├── 🌐 web/             Next.js 15 web application
├── ⚡ backend/         FastAPI REST API + WebSocket
├── 🤖 ai_models/       YOLOv8 + SAM2 + EfficientNetV2 + MiDaS
├── 📊 analytics/       Nutrition Memory Engine
├── 💡 recommendation/  LightGBM recommendation engine
└── 📦 datasets/        Dataset download & preprocessing scripts
```

## 🚀 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Mobile** | Flutter 3.x, Dart, Material 3, Riverpod |
| **Web** | Next.js 15, TypeScript, Tailwind CSS, ShadCN UI |
| **Backend** | FastAPI, Python 3.11, SQLAlchemy, Alembic |
| **Database** | PostgreSQL 16, Redis 7 |
| **AI Vision** | YOLOv8, SAM2, EfficientNetV2, MiDaS |
| **AI NLP** | Gemini 2.5 Pro (Google AI) |
| **ML** | LightGBM, PyTorch, TorchVision |
| **Nutrition APIs** | USDA FoodData Central, OpenFoodFacts, Indian FCD |
| **Auth** | JWT, Google OAuth 2.0 |
| **Deployment** | Docker, Docker Compose, Nginx, GitHub Actions |

---

## ✨ Features

### 📸 Multimodal Food Analysis
- **Camera capture** or **gallery upload** on mobile
- **YOLOv8** – detect multiple food items with bounding boxes
- **SAM2** – precise food segmentation masks
- **EfficientNetV2** – classify 256+ food categories
- **MiDaS** – depth estimation for portion size & volume

### 🍎 Comprehensive Nutrition Tracking
- Calories, protein, carbs, fat, fiber, sugar, sodium
- Vitamins (A, B, C, D, E, K), minerals (Ca, Fe, Mg, Zn)
- Data from USDA FoodData Central + OpenFoodFacts + Indian FCD
- Supports 4 datasets: Food-101, UECFood256, Nutrition5K, Recipe1M

### 👤 User Profiles
- Age, gender, height, weight, BMI, activity level
- Health conditions: diabetes, hypertension, PCOS, thyroid, etc.
- Goals: weight loss, muscle gain, maintenance, diabetes management

### 🧠 Nutrition Memory Engine
- Daily, weekly, monthly trend tracking
- Calorie & macro intake trends
- Deficiency detection & alerts
- Consistency score & streaks

### 💡 Personalized Recommendations
- LightGBM ML model + rule-based health logic
- Context-aware meal suggestions
- Goal-based dietary planning
- Disease-condition aware recommendations

### 🤖 Gemini AI Nutrition Coach
- Conversational AI powered by Gemini 2.5 Pro
- Personalized meal advice & Q&A
- Intelligent daily, weekly, monthly summaries
- Smart insights from stored analytics

### 📊 Premium Dashboard
- Nutrition charts (Recharts/Chart.js)
- Progress tracking & goal monitoring
- Meal timeline & history
- Workout suggestions
- Streak tracking

---

## 🛠️ Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.11+
- Flutter 3.x SDK

### 1. Clone & Configure
```bash
git clone https://github.com/Swyamk/ResearchI.git
cd ResearchI
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start with Docker
```bash
docker-compose up -d
```

### 3. Run Migrations
```bash
docker-compose exec backend alembic upgrade head
```

### 4. Download Datasets (Optional)
```bash
cd datasets && bash download_datasets.sh
```

### 5. Access Services
| Service | URL |
|---------|-----|
| Web App | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| API ReDoc | http://localhost:8000/redoc |
| PgAdmin | http://localhost:5050 |
| Redis Commander | http://localhost:8081 |

---

## 📁 Project Structure

```
ResearchI/
├── .env.example
├── docker-compose.yml
├── docker-compose.prod.yml
├── .github/workflows/
│   ├── ci.yml
│   └── cd.yml
│
├── backend/                    # FastAPI
│   ├── app/
│   │   ├── api/v1/            # Route handlers
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   └── core/              # Security, deps
│   └── migrations/            # Alembic migrations
│
├── ai_models/                 # Computer Vision AI
│   ├── inference/             # Detection, segmentation, classification
│   └── training/              # Training scripts
│
├── analytics/                 # Nutrition Memory Engine
├── recommendation/            # LightGBM + Rule Engine
├── datasets/                  # Dataset management
│
├── web/                       # Next.js 15
│   └── src/
│       ├── app/               # App Router pages
│       ├── components/        # UI components
│       ├── lib/               # Utilities
│       └── hooks/             # Custom hooks
│
└── mobile/                    # Flutter
    └── lib/
        ├── features/          # Feature modules
        └── core/              # Core utilities
```

---

## 🔑 Environment Variables

See [`.env.example`](.env.example) for all required environment variables.

Key variables:
- `GEMINI_API_KEY` – Google AI Gemini API key
- `USDA_API_KEY` – USDA FoodData Central API key
- `GOOGLE_CLIENT_ID` – Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` – Google OAuth client secret
- `DATABASE_URL` – PostgreSQL connection string
- `REDIS_URL` – Redis connection string
- `SECRET_KEY` – JWT secret key

---

## 🧪 API Documentation

Once running, access interactive API docs at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key API Endpoints
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
GET    /api/v1/auth/google
POST   /api/v1/meals/analyze         # Upload food image
GET    /api/v1/meals/history
GET    /api/v1/analytics/daily
GET    /api/v1/analytics/weekly
GET    /api/v1/analytics/monthly
POST   /api/v1/ai-coach/chat         # Gemini AI chat
GET    /api/v1/recommendations/today
```

---

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| backend | 8000 | FastAPI API server |
| ai_models | 8001 | AI inference service |
| web | 3000 | Next.js web app |
| postgres | 5432 | PostgreSQL database |
| redis | 6379 | Redis cache |
| nginx | 80/443 | Reverse proxy |
| pgadmin | 5050 | DB admin UI |

---

## 📊 Datasets

| Dataset | Size | Purpose |
|---------|------|---------|
| Food-101 | ~5GB | 101 food categories, 101k images |
| UECFood256 | ~2GB | 256 food categories, 31k images |
| Nutrition5K | ~8GB | Depth + nutrition ground truth |
| Recipe1M | ~30GB | 1M recipes for ingredient parsing |

Download via: `cd datasets && bash download_datasets.sh`

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License – see [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

Built with ❤️ by [Swyam Kumar](https://github.com/Swyamk)