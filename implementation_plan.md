# NutriMind – Personalized Multimodal Nutrition Intelligence System

## Overview
Production-ready full-stack AI application combining computer vision, NLP, and personalized health analytics for intelligent nutrition tracking.

## Folder Structure

```
ResearchI/
├── README.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
│
├── backend/                          # FastAPI Backend
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── redis_client.py
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── users.py
│   │   │   │   ├── meals.py
│   │   │   │   ├── nutrition.py
│   │   │   │   ├── analytics.py
│   │   │   │   ├── recommendations.py
│   │   │   │   └── ai_coach.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── meal.py
│   │   │   ├── nutrition.py
│   │   │   └── analytics.py
│   │   ├── schemas/
│   │   │   ├── user.py
│   │   │   ├── meal.py
│   │   │   ├── nutrition.py
│   │   │   └── analytics.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── meal_service.py
│   │   │   ├── nutrition_service.py
│   │   │   ├── analytics_service.py
│   │   │   ├── recommendation_service.py
│   │   │   └── gemini_service.py
│   │   └── core/
│   │       ├── security.py
│   │       └── dependencies.py
│   └── migrations/
│
├── ai_models/                        # AI/ML Pipeline
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── inference/
│   │   ├── food_detector.py          # YOLOv8
│   │   ├── food_segmentor.py         # SAM2
│   │   ├── food_classifier.py        # EfficientNetV2
│   │   ├── depth_estimator.py        # MiDaS
│   │   └── pipeline.py              # Full inference pipeline
│   ├── training/
│   │   ├── train_detector.py
│   │   ├── train_classifier.py
│   │   └── utils.py
│   └── models/                       # Model weights (gitignored)
│
├── datasets/                         # Dataset management
│   ├── download_datasets.sh
│   ├── preprocess_food101.py
│   ├── preprocess_uecfood256.py
│   ├── preprocess_nutrition5k.py
│   └── preprocess_recipe1m.py
│
├── web/                              # Next.js 15 Web App
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── dashboard/
│   │   │   ├── meals/
│   │   │   ├── analytics/
│   │   │   ├── ai-coach/
│   │   │   ├── profile/
│   │   │   └── auth/
│   │   ├── components/
│   │   │   ├── ui/                  # ShadCN components
│   │   │   ├── dashboard/
│   │   │   ├── meals/
│   │   │   ├── charts/
│   │   │   └── ai-chat/
│   │   ├── lib/
│   │   └── hooks/
│
├── mobile/                           # Flutter Mobile App
│   ├── pubspec.yaml
│   ├── lib/
│   │   ├── main.dart
│   │   ├── app/
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   ├── camera/
│   │   │   ├── dashboard/
│   │   │   ├── meals/
│   │   │   ├── analytics/
│   │   │   └── ai_coach/
│   │   ├── core/
│   │   └── shared/
│
├── analytics/                        # Nutrition Memory Engine
│   ├── nutrition_memory.py
│   ├── trend_analyzer.py
│   └── deficiency_detector.py
│
└── recommendation/                   # LightGBM Recommendation Engine
    ├── recommendation_engine.py
    ├── lightgbm_model.py
    └── rule_engine.py
```

## Components to Build

### 1. Backend (FastAPI)
- JWT + Google OAuth authentication
- CRUD APIs for users, meals, nutrition
- Analytics aggregation endpoints
- Gemini AI integration endpoint
- WebSocket for real-time AI chat

### 2. AI Models
- YOLOv8 food detection
- SAM2 food segmentation
- EfficientNetV2 food classification
- MiDaS depth/portion estimation
- Full inference pipeline

### 3. Nutrition Data
- USDA FoodData Central API integration
- OpenFoodFacts API integration
- Indian Food Composition dataset

### 4. Web App (Next.js 15)
- Dashboard with nutrition charts
- Meal logging with image upload
- AI Coach chat interface
- Analytics & trends
- Profile management

### 5. Mobile App (Flutter)
- Camera integration
- Image capture & upload
- Dashboard & meal history
- AI Chat interface

### 6. Database (PostgreSQL)
- Users, profiles, health conditions
- Meals, food items, nutrition data
- Analytics snapshots
- AI conversation history

### 7. Caching (Redis)
- Session management
- Nutrition data caching
- Rate limiting

### 8. Deployment
- Docker Compose (dev + prod)
- GitHub Actions CI/CD
- Nginx reverse proxy

## Execution Order
1. Project structure & configs
2. Database schema & migrations
3. FastAPI backend core
4. AI inference pipeline
5. Nutrition data integrations
6. Analytics & recommendation engines
7. Next.js web app
8. Flutter mobile app
9. Docker & deployment configs
10. Dataset download scripts
11. CI/CD workflows
