import json
from sqlalchemy.orm import Session
from groq import Groq

from app.core.config import settings
from app.schemas.ai import AIInsightsResponse
from app.services.repository_service import get_repository_by_id
from app.services.health_service import calculate_health_score
from app.services.dormancy_service import calculate_dormancy


def get_ai_insights(db: Session, repository_id: int) -> AIInsightsResponse:
    # 1. Retrieve repository (raises ValueError if not found)
    repository = get_repository_by_id(db, repository_id)

    # 2. Reuse health_score
    health_score, health_grade, health_summary = calculate_health_score(repository)

    # 3. Reuse dormancy status
    days_since_push, dormancy_status, dormancy_message = calculate_dormancy(repository)

    # 4. Build prompt
    prompt = (
        f"Analyze the repository details:\n"
        f"- Name: {repository.name}\n"
        f"- Full Name: {repository.full_name}\n"
        f"- Description: {repository.description}\n"
        f"- Language: {repository.language}\n"
        f"- Default Branch: {repository.default_branch}\n"
        f"- Stars: {repository.stars}\n"
        f"- Forks: {repository.forks}\n"
        f"- Open Issues: {repository.open_issues}\n"
        f"- Size: {repository.size} KB\n"
        f"- Health Score: {health_score} (Grade: {health_grade})\n"
        f"- Health Summary: {health_summary}\n"
        f"- Dormancy Status: {dormancy_status} ({days_since_push} days since last push)\n"
    )

    # 5. Send to Groq and parse response
    try:
        api_key = settings.groq_api_key
        client = Groq(api_key=api_key)

        system_prompt = (
            "You are a repository analysis assistant. Analyze the repository metadata and metrics and return insights. "
            "You must return a valid JSON object matching the following structure:\n"
            "{\n"
            "  \"repository_name\": \"string\",\n"
            "  \"summary\": \"string\",\n"
            "  \"strengths\": [\"string\"],\n"
            "  \"weaknesses\": [\"string\"],\n"
            "  \"suggestions\": [\"string\"],\n"
            "  \"beginner_friendly\": true/false,\n"
            "  \"complexity\": \"Low\"/\"Medium\"/\"High\",\n"
            "  \"ai_score\": float\n"
            "}\n"
            "Respond ONLY with this JSON object."
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            model=settings.groq_model,
            response_format={"type": "json_object"},
        )

        content = chat_completion.choices[0].message.content
        data = json.loads(content)

        return AIInsightsResponse(
            repository_name=data.get("repository_name", repository.name),
            summary=data.get("summary", ""),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            suggestions=data.get("suggestions", []),
            beginner_friendly=bool(data.get("beginner_friendly", False)),
            complexity=data.get("complexity", "Medium"),
            ai_score=float(data.get("ai_score", 0.0)),
        )
    except Exception as e:
        raise RuntimeError(f"AI service call failed: {str(e)}") from e
