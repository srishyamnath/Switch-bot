# lead_parser.py
import re

def parse_lead_info(text):
    """
    Parses a given text message to extract potential lead information
    like name, email, and phone number.
    """
    lead_info = {
        "name": None,
        "email": None,
        "phone": None
    }

    # Email extraction (basic regex)
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    if email_match:
        lead_info["email"] = email_match.group(0)

    # Phone number extraction (basic regex, adjust for specific formats if known)
    # This regex looks for 10-15 digits, possibly with spaces, hyphens, or parentheses
    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    if phone_match:
        # Clean up the phone number to be just digits
        phone_number = re.sub(r'[^\d]', '', phone_match.group(0))
        if 10 <= len(phone_number) <= 15: # Basic validation for length
            lead_info["phone"] = phone_number

    # Placeholder for name extraction - this is usually the hardest without context
    # For now, we'll assume name is collected separately or from explicit input.
    return lead_info

# Example Usage (for testing the parser itself)
if __name__ == "__main__":
    test_messages = [
        "Hi, I'm John Doe, my email is john.doe@example.com and phone is +91-9876543210.",
        "Contact me at jane.smith@test.org or call 080-12345678.",
        "My number is 9988776655. Name: Alice Brown.",
        "Just a random message without contact info."
    ]

    for msg in test_messages:
        parsed = parse_lead_info(msg)
        print(f"Original: '{msg}'")
        print(f"Parsed: Name={parsed['name']}, Email={parsed['email']}, Phone={parsed['phone']}\n")