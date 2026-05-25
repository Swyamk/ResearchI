"""
Gemini AI Service – NutriMind's conversational nutrition coach.
Powered by Gemini 2.5 Pro for personalized advice, summaries, and Q&A.
"""
import json
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional

import google.generativeai as genai
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import AIConversation, User

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

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


class GeminiService:
    """Service for Gemini AI integration."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            system_instruction=SYSTEM_PROMPT,
            generation_config=genai.GenerationConfig(
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
                temperature=settings.GEMINI_TEMPERATURE,
            ),
        )

    def _build_user_context(self, user: User) -> str:
        """Build a context string from the user's health profile."""
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
        """Retrieve recent conversation history for context."""
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
            {"role": msg.role, "parts": [msg.content]}
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
        """Save a conversation message to the database."""
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
        """Send a message and get a response from Gemini AI."""
        user_context = self._build_user_context(user)
        history = await self._get_conversation_history(user.id, session_id)

        # Build enhanced message with user context
        enhanced_message = f"{user_context}\n\n---\nUser Question: {message}"
        if context_type:
            enhanced_message = f"[Context: {context_type}]\n{enhanced_message}"

        # Start chat with history
        chat = self.model.start_chat(history=history)

        try:
            response = await chat.send_message_async(enhanced_message)
            response_text = response.text
            tokens_used = response.usage_metadata.total_token_count if response.usage_metadata else None
        except Exception as e:
            response_text = f"I'm having trouble connecting right now. Please try again in a moment. (Error: {str(e)[:100]})"
            tokens_used = None

        # Save messages to DB
        await self._save_message(user.id, session_id, "user", message)
        await self._save_message(
            user.id, session_id, "model", response_text,
            tokens_used=tokens_used,
            context={"context_type": context_type},
        )

        # Extract quick suggestions from response
        suggestions = self._extract_suggestions(response_text)

        return {
            "response": response_text,
            "tokens_used": tokens_used,
            "suggestions": suggestions,
        }

    async def stream_chat(
        self,
        user: User,
        message: str,
        session_id: str,
    ) -> AsyncGenerator[str, None]:
        """Stream chat response chunks."""
        user_context = self._build_user_context(user)
        history = await self._get_conversation_history(user.id, session_id)
        enhanced_message = f"{user_context}\n\n---\nUser Question: {message}"

        chat = self.model.start_chat(history=history)
        full_response = ""

        try:
            async for chunk in await chat.send_message_async(enhanced_message, stream=True):
                text = chunk.text
                full_response += text
                yield json.dumps({"chunk": text})
        except Exception as e:
            error_msg = "I'm experiencing connection issues. Please try again."
            yield json.dumps({"chunk": error_msg})
            full_response = error_msg

        # Save to DB
        await self._save_message(user.id, session_id, "user", message)
        await self._save_message(user.id, session_id, "model", full_response)

    async def stream_chat_ws(
        self,
        user_id: str,
        message: str,
        session_id: str,
    ) -> AsyncGenerator[str, None]:
        """Stream response for WebSocket (without user object)."""
        try:
            response = self.model.generate_content(message, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"Connection error: {str(e)[:100]}"

    async def generate_daily_summary(self, user: User) -> str:
        """Generate an AI daily nutrition summary from today's data."""
        user_context = self._build_user_context(user)

        # Get today's analytics context
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
        response = await self.model.generate_content_async(prompt)
        return response.text

    async def generate_weekly_summary(self, user: User) -> str:
        """Generate AI weekly nutrition summary."""
        user_context = self._build_user_context(user)

        prompt = f"""
{user_context}

Please generate a comprehensive weekly nutrition analysis for this user.
Include:
1. Overall performance this week (consistency, goals achieved)
2. Nutritional patterns (what they're getting right/wrong)
3. Progress toward their primary goal ({user.profile.primary_goal.value if user.profile and user.profile.primary_goal else 'general wellness'})
4. Top 3 improvements for next week
5. Celebration of wins with a motivating message

Keep it comprehensive but readable (250-400 words).
"""
        response = await self.model.generate_content_async(prompt)
        return response.text

    async def generate_monthly_summary(self, user: User) -> str:
        """Generate AI monthly nutrition report."""
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
        response = await self.model.generate_content_async(prompt)
        return response.text

    def _extract_suggestions(self, text: str) -> List[str]:
        """Extract quick follow-up suggestions from AI response."""
        suggestions = [
            "Tell me more about this",
            "What should I eat tomorrow?",
            "How can I improve my protein intake?",
            "Give me a meal plan for my goals",
        ]
        return suggestions[:3]
