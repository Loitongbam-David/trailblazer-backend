from groq import Groq
from app.config import settings

client = Groq(api_key=settings.groq_api_key)

MODEL = "openai/gpt-oss-120b"

# ─────────────────────────────────────────────
# 1. CONTENT SYNTHESIS — Study Guide Generator
# ─────────────────────────────────────────────

async def synthesize_study_guide(
    topic_title: str,
    topic_description: str,
    raw_context: str = ""
) -> str:
    """
    Takes a topic + optional raw context (scraped web data, outlines)
    and generates a clean Markdown study guide using Llama.
    """

    system_prompt = """You are an expert educational content writer.
Your job is to transform raw topic information into a clean, structured study guide.

FORMAT RULES — follow exactly:
- Start with a # heading (the topic title)
- Use ## for major sections: Overview, Key Concepts, Deep Dive, Examples, Summary
- Use ### for subsections
- Use bullet points for lists
- Use ```language code blocks for all code examples
- Use **bold** for key terms on first use
- Use > blockquotes for important notes or warnings
- End with a ## Quick Recap section with 3-5 bullet points

TONE: Encouraging, clear, and precise. Write as if explaining to a motivated student.
NEVER add filler phrases like "Great question!" or "In conclusion".
NEVER go off-topic. Stay strictly within the subject provided."""

    user_prompt = f"""Create a comprehensive study guide for the following topic:

TOPIC: {topic_title}
DESCRIPTION: {topic_description}

ADDITIONAL CONTEXT (use this to enrich the guide):
{raw_context if raw_context else "No additional context provided — use your knowledge."}

Generate the full Markdown study guide now."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=2048,
    )

    return response.choices[0].message.content


# ─────────────────────────────────────────────
# 2. CONTEXT-AWARE AI TUTOR — Chatbot
# ─────────────────────────────────────────────

async def tutor_chat(
    user_message: str,
    active_topic_title: str,
    active_topic_description: str,
    conversation_history: list[dict]
) -> str:
    """
    Context-locked AI tutor. The system prompt forcefully binds
    the AI to only answer within the active topic's scope.

    conversation_history: list of {role: 'user'|'assistant', content: str}
    """

    system_prompt = f"""You are Trailblazer AI, an expert and encouraging tutor.

YOUR ACTIVE TEACHING CONTEXT — THIS IS YOUR ONLY ALLOWED SUBJECT:
Topic: {active_topic_title}
Description: {active_topic_description}

STRICT RULES:
1. You ONLY answer questions related to "{active_topic_title}". 
2. If the user asks about ANYTHING outside this topic, respond with:
   "I'm your dedicated tutor for **{active_topic_title}**. Let's stay focused! 
   Ask me anything about this topic and I'll help you master it."
3. Never answer questions about other programming languages, frameworks, 
   or topics not directly related to {active_topic_title}.
4. Always use simple analogies before technical explanations.
5. When showing code, always use fenced code blocks with the language specified.
6. End every explanation with a follow-up question to check understanding.
7. Be warm, patient, and encouraging — never condescending.
8. Keep responses concise (under 300 words) unless a code example requires more.

PERSONA: You are knowledgeable but approachable. You celebrate small wins."""

    # Build messages array: system + full history + new message
    messages = [{"role": "system", "content": system_prompt}]
    
    # Include last 10 messages for context window efficiency
    recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
    messages.extend(recent_history)
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.6,
        max_tokens=1024,
    )

    return response.choices[0].message.content


# ─────────────────────────────────────────────
# 3. TOPIC DESCRIPTION GENERATOR (bonus utility)
# ─────────────────────────────────────────────

async def generate_topic_description(topic_title: str) -> str:
    """
    Generates a concise 2-3 sentence topic description
    used when seeding new topics into the curriculum.
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # lighter model for short tasks
        messages=[
            {
                "role": "user",
                "content": f"""Write a 2-3 sentence description for a learning topic called "{topic_title}".
Be concise and informative. Describe what the student will learn and why it matters.
No filler phrases. Output only the description."""
            }
        ],
        temperature=0.5,
        max_tokens=150,
    )

    return response.choices[0].message.content