import anthropic
from dotenv import load_dotenv
from agents.state import AgentState

load_dotenv()


def narrative_node(state: AgentState) -> AgentState:
    client = anthropic.Anthropic()
    rankings = state.get("rankings", [])
    anomalies = state.get("anomalies", [])

    top5 = [
        f"{r['rank']}. {r['title']} ({r['media_type']}, popularity: {float(r['popularity']):.1f})"
        for r in rankings[:5]
    ]

    anomaly_section = ""
    if anomalies:
        anomaly_titles = ", ".join(r["title"] for r in anomalies)
        anomaly_section = f"\n\nAnomaly detected — unusually high popularity: {anomaly_titles}."

    prompt = (
        "You are a media analyst. Respond in EXACTLY this format with no extra text:\n\n"
        "HEADLINE: <one punchy sentence under 12 words>\n"
        "COMMENTARY: <exactly 3 sentences with specific titles and numbers>\n\n"
        "Example:\n"
        "HEADLINE: NCIS leads a nostalgia wave dominating this week's trending charts\n"
        "COMMENTARY: Procedural crime dramas dominate today with NCIS at 236.2 popularity. "
        "Action titles account for 4 of the top 10 slots this cycle. "
        "Streaming originals are gaining ground with 3 new entries in the top 5.\n\n"
        "Today's trending media:\n\n"
        + "\n".join(top5)
        + anomaly_section
    )

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text

    parts = raw.split("COMMENTARY:", 1)
    headline = parts[0].replace("HEADLINE:", "").strip().replace("\n", " ")
    commentary = parts[1].strip().replace("\n", " ") if len(parts) > 1 else ""

    titles_mentioned = [r["title"] for r in rankings[:5]]
    top = rankings[0] if rankings else {}

    return {**state, "commentary": {
        "headline": headline,
        "commentary": commentary,
        "titles_mentioned": titles_mentioned,
        "top_title": top.get("title"),
        "top_media_type": top.get("media_type"),
    }}
