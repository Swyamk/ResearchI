"""
AI Coach Service – NutriMind's conversational nutrition coach.
Powered by Groq (llama-3.3-70b-versatile) via OpenAI-compatible API.
"""
import json
import os
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from openai import AsyncOpenAI
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AIConversation, User

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = os.environ.get("GROQ_CHAT_MODEL", "llama-3.3-70b-versatile")

SYSTEM_PROMPT = """You are NutriMind AI, an expert personalized nutrition coach powered by advanced AI.
You have deep knowledge of:
- Nutrition science, macronutrients, micronutrients, and dietary guidelines
- Indian cuisine and global food culture
- Medical nutrition therapy for diabetes, hypertension, PCOS, thyroid disorders, etc.
- Weight management, muscle building, and athletic performance
- Ayurvedic and modern nutritional principles

Your role:
1. Analyze meals and provide accurate nutritional insights
2. Give personalized advice based on the user's health profile, goals, and conditions
3. Answer questions about food, nutrients, and healthy eating
4. Generate actionable, motivating daily/weekly/monthly summaries
5. Suggest meal improvements and healthier alternatives

Guidelines:
- Be warm, encouraging, and professional
- Use simple language while being scientifically accurate
- Always consider the user's specific health conditions and goals
- Provide practical, actionable advice
- When discussing Indian foods, use both English and Hindi/local names
- Always remind users that AI advice doesn't replace medical consultation
- Keep responses concise but comprehensive (aim for 150-300 words unless asked for detail)
"""


def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=os.environ["GROQ_API_KEY"],
        base_url=GROQ_BASE_URL,
    )


class GeminiService:
    """AI Coach service — backed by Groq instead of Gemini."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = _get_client()

    def _build_user_context(self, user: User) -> str:
        profile = user.profile
        if not profile:
            return f"User: {user.full_name}"

        parts = [f"User Profile for {user.full_name}:"]
        if profile.age:
            parts.append(f"- Age: {profile.age}")
        if profile.gender:
            parts.append(f"- Gender: {profile.gender.value}")
        if profile.weight_kg and profile.height_cm:
            parts.append(f"- Weight: {profile.weight_kg}kg, Height: {profile.height_cm}cm")
        if profile.bmi:
            parts.append(f"- BMI: {profile.bmi}")
        if profile.activity_level:
            parts.append(f"- Activity Level: {profile.activity_level.value}")
        if profile.primary_goal:
            parts.append(f"- Primary Goal: {profile.primary_goal.value}")
        if profile.health_conditions:
            parts.append(f"- Health Conditions: {', '.join(profile.health_conditions)}")
        if profile.dietary_restrictions:
            parts.append(f"- Dietary Restrictions: {', '.join(profile.dietary_restrictions)}")
        if profile.daily_calorie_target:
            parts.append(f"- Daily Calorie Target: {profile.daily_calorie_target} kcal")
        if profile.daily_protein_target_g:
            parts.append(f"- Protein Target: {profile.daily_protein_target_g}g/day")

        return "\n".join(parts)

    async def _get_conversation_history(
        self, user_id: uuid.UUID, session_id: str, limit: int = 10
    ) -> List[Dict]:
        result = await self.db.execute(
            select(AIConversation)
            .where(
                AIConversation.user_id == user_id,
                AIConversation.session_id == session_id,
            )
            .order_by(desc(AIConversation.created_at))
            .limit(limit)
        )
        messages = list(reversed(result.scalars().all()))
        return [
            {
                "role": "assistant" if msg.role == "model" else msg.role,
                "content": msg.content,
            }
            for msg in messages
        ]

    async def _save_message(
        self,
        user_id: uuid.UUID,
        session_id: str,
        role: str,
        content: str,
        tokens_used: Optional[int] = None,
        context: Optional[dict] = None,
    ):
        msg = AIConversation(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            tokens_used=tokens_used,
            context=context,
        )
        self.db.add(msg)
        await self.db.commit()

    async def chat(
        self,
        user: User,
        message: str,
        session_id: str,
        context_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        user_context = self._build_user_context(user)
        history = await self._get_conversation_history(user.id, session_id)

        enhanced_message = f"{user_context}\n\n---\nUser Question: {message}"
        if context_type:
            enhanced_message = f"[Context: {context_type}]\n{enhanced_message}"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": enhanced_message},
        ]

        try:
            response = await self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
            )
            response_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else None
        except Exception as e:
            response_text = f"I'm having trouble connecting right now. Please try again in a moment. (Error: {str(e)[:100]})"
            tokens_used = None

        await self._save_message(user.id, session_id, "user", message)
        await self._save_message(
            user.id, session_id, "model", response_text,
            tokens_used=tokens_used,
            context={"context_type": context_type},
        )

        return {
            "response": response_text,
            "tokens_used": tokens_used,
            "suggestions": self._extract_suggestions(response_text),
        }

    async def stream_chat(
        self,
        user: User,
        message: str,
        session_id: str,
    ) -> AsyncGenerator[str, None]:
        user_context = self._build_user_context(user)
        history = await self._get_conversation_history(user.id, session_id)
        enhanced_message = f"{user_context}\n\n---\nUser Question: {message}"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *history,
            {"role": "user", "content": enhanced_message},
        ]

        full_response = ""
        try:
            stream = await self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
                stream=True,
            )
            async for chunk in stream:
                text = chunk.choices[0].delta.content or ""
                if text:
                    full_response += text
                    yield json.dumps({"chunk": text})
        except Exception as e:
            error_msg = "I'm experiencing connection issues. Please try again."
            yield json.dumps({"chunk": error_msg})
            full_response = error_msg

        await self._save_message(user.id, session_id, "user", message)
        await self._save_message(user.id, session_id, "model", full_response)

    async def stream_chat_ws(
        self,
        user_id: str,
        message: str,
        session_id: str,
    ) -> AsyncGenerator[str, None]:
        try:
            stream = await self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                max_tokens=1024,
                temperature=0.7,
                stream=True,
            )
            async for chunk in stream:
                text = chunk.choices[0].delta.content or ""
                if text:
                    yield text
        except Exception as e:
            yield f"Connection error: {str(e)[:100]}"

    async def _generate_text(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1024,
            temperature=0.7,
        )
        return response.choices[0].message.content

    async def generate_daily_summary(self, user: User) -> str:
        user_context = self._build_user_context(user)

        from app.services.analytics_service import AnalyticsService
        analytics_service = AnalyticsService(self.db)
        try:
            dashboard = await analytics_service.get_dashboard_summary(user)
            nutrition_context = f"""
Today's Nutrition Summary:
- Calories: {dashboard.today_calories:.0f} / {dashboard.calorie_target or 'N/A'} kcal
- Protein: {dashboard.today_protein_g:.1f}g
- Carbs: {dashboard.today_carbs_g:.1f}g
- Fat: {dashboard.today_fat_g:.1f}g
- Fiber: {dashboard.today_fiber_g:.1f}g
- Sugar: {dashboard.today_sugar_g:.1f}g
- Water: {dashboard.today_water_ml:.0f}ml
- Meals logged: {dashboard.meals_today}
- Nutrition Score: {dashboard.nutrition_score:.0f}/100
- Current Streak: {dashboard.streak.current_streak} days
"""
        except Exception:
            nutrition_context = "Today's nutrition data is being collected."

        prompt = f"""
{user_context}

{nutrition_context}

Please generate a warm, encouraging, and insightful daily nutrition summary for this user.
Include:
1. Key achievements today
2. Areas that need attention
3. 2-3 specific actionable tips for tomorrow
4. A motivating closing message

Keep it personal, friendly, and under 300 words.
"""
        return await self._generate_text(prompt)

    async def generate_weekly_summary(self, user: User) -> str:
        user_context = self._build_user_context(user)
        goal = user.profile.primary_goal.value if user.profile and user.profile.primary_goal else "general wellness"
        prompt = f"""
{user_context}

Please generate a comprehensive weekly nutrition analysis for this user.
Include:
1. Overall performance this week (consistency, goals achieved)
2. Nutritional patterns (what they're getting right/wrong)
3. Progress toward their primary goal ({goal})
4. Top 3 improvements for next week
5. Celebration of wins with a motivating message

Keep it comprehensive but readable (250-400 words).
"""
        return await self._generate_text(prompt)

    async def generate_monthly_summary(self, user: User) -> str:
        user_context = self._build_user_context(user)
        prompt = f"""
{user_context}

Please generate a comprehensive monthly nutrition report for this user.
Include:
1. Monthly progress overview
2. Key trends (improving/declining areas)
3. Goal progress assessment
4. Top achievements of the month
5. Focus areas for next month
6. Long-term health insights
7. Personalized recommendations based on health conditions

Tone: Professional yet warm, like a personal nutrition coach. (400-600 words)
"""
        return await self._generate_text(prompt)

    def _extract_suggestions(self, _text: str) -> List[str]:
        return [
            "Tell me more about this",
            "What should I eat tomorrow?",
            "How can I improve my protein intake?",
        ]
