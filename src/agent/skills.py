import re
from typing import Dict, Any

class AgentSkills:
    """Formal skills for the Digital FTE as defined in Exercise 1.5."""

    @staticmethod
    def analyze_sentiment(text: str) -> Dict[str, Any]:
        """
        Sentiment Analysis Skill: Scores text based on emotional keywords.
        Returns score (0.0 to 1.0) and confidence.
        """
        negative_words = ["garbage", "trash", "broken", "sue", "lawyer", "refund", "worst", "slow", "buggy"]
        positive_words = ["love", "great", "helpful", "thanks", "awesome", "perfect"]
        
        text_lower = text.lower()
        score = 0.5  # Neutral starting point
        
        for word in negative_words:
            if word in text_lower:
                score -= 0.15
        
        for word in positive_words:
            if word in text_lower:
                score += 0.1
        
        # Clamp score between 0.0 and 1.0
        score = max(0.0, min(1.0, round(score, 2)))
        
        return {
            "sentiment_score": score,
            "confidence": 0.8,
            "is_angry": score < 0.3
        }

    @staticmethod
    def adapt_channel(text: str, channel: str) -> str:
        """
        Channel Adaptation Skill: Formats text appropriately for the medium.
        """
        channel = channel.lower()
        if channel == "whatsapp":
            # Concise, no signature, emojis
            return f"Flowie: {text} ✅"
        elif channel == "email":
            # Formal with signature
            return (
                "Hello,\n\n"
                f"{text}\n\n"
                "Best regards,\n"
                "The SaaSFlow Success Team"
            )
        else:
            # Default/Web Form: Structured
            return f"**SaaSFlow Support**: {text}"

if __name__ == "__main__":
    skills = AgentSkills()
    print(f"Sentiment (Angry): {skills.analyze_sentiment('This is trash, I am suing!')}")
    print(f"WhatsApp Format: {skills.adapt_channel('How to add a task?', 'whatsapp')}")
    print(f"Email Format: {skills.adapt_channel('How to add a task?', 'email')}")
