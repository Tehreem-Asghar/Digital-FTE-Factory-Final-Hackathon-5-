# formatters.py

def format_email_response(message: str, customer_name: str = "Customer") -> str:
    """Formats a formal email response."""
    return (
        f"Hello {customer_name},\n\n"
        f"{message}\n\n"
        "If you have any further questions, please don't hesitate to reply to this email.\n\n"
        "Best regards,\n"
        "The SaaSFlow Success Team"
    )

def format_whatsapp_response(message: str) -> str:
    """Formats a concise WhatsApp response."""
    # Keep it short, maybe add a brand prefix or emoji as per brand-voice
    formatted = f"Flowie: {message}"
    if len(formatted) > 300:
        formatted = formatted[:297] + "..."
    return f"{formatted} ✅"

def format_for_channel(message: str, channel: str, customer_name: str = "Customer") -> str:
    """Universal formatter based on channel."""
    channel = channel.lower()
    if channel == "email":
        return format_email_response(message, customer_name)
    elif channel == "whatsapp":
        return format_whatsapp_response(message)
    else:
        return f"SaaSFlow Support: {message}"
