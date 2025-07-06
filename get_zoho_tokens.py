# get_zoho_tokens.py
import requests
import json
import time # This import might not have been in your original, but it's used if we expand for token expiry management

# --- IMPORTANT: REPLACE THESE VALUES WITH YOUR ACTUAL CREDENTIALS ---
# These are from Zoho API Console
CLIENT_ID = "1000.CSHGEBS3UWDNBS8TSVI76M8NWXPFKC"
CLIENT_SECRET = "3aa63f075e19d9a39a312dd18b15e393b15826ad92"

# This is the short-lived code you copied from the browser URL after redirecting
# Based on your image_40492b.jpg, this is your Grant Code:
GRANT_CODE = "1000.dedf0ac2963f6e161c526ca75a506272.caab0c5c77c6ada3411031d1327708c7"

# This MUST exactly match the Authorized Redirect URI you configured in Zoho API Console
REDIRECT_URI = "https://www.zoho.in"

# Zoho accounts URL for token exchange (for .in domain)
ZOHO_ACCOUNTS_URL = "https://accounts.zoho.in/oauth/v2/token"

params = {
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "code": GRANT_CODE,
    "redirect_uri": REDIRECT_URI
}

print("Attempting to get Zoho refresh token...")
print(f"DEBUG: Using CLIENT_ID={CLIENT_ID[:5]}... CLIENT_SECRET={CLIENT_SECRET[:5]}... GRANT_CODE={GRANT_CODE[:5]}... REDIRECT_URI={REDIRECT_URI}") # THIS IS THE DEBUG LINE
try:
    response = requests.post(ZOHO_ACCOUNTS_URL, params=params)
    response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
    data = response.json()

    print("\n--- Zoho Token Response ---")
    print(json.dumps(data, indent=4))

    if "refresh_token" in data:
        print("\nSUCCESS! Your Zoho Refresh Token is:")
        print(data["refresh_token"])
        print("\nIMPORTANT: Copy this 'refresh_token' value and save it in your config/crm_config.json file.")
        print("You can now delete this get_zoho_tokens.py file if you wish.")
    else:
        print("\nFAILED to get refresh token. Response data:")
        print(json.dumps(data, indent=4))
        print("\nTroubleshooting:")
        print("- Ensure GRANT_CODE is correct and NOT EXPIRED (it's very short-lived!).")
        print("- Double-check CLIENT_ID, CLIENT_SECRET, and REDIRECT_URI for exact matches.")
        print("- Verify your ZOHO_ACCOUNTS_URL is correct for your Zoho domain (.com, .eu, .in, etc.).")
        print("- Check your network connection.")

except requests.exceptions.RequestException as e:
    print(f"\nNetwork or API error: {e}")
    if e.response is not None:
        print(f"Response status code: {e.response.status_code}")
        print(f"Response content: {e.response.text}")
except json.JSONDecodeError:
    print("\nError: Could not decode JSON response from Zoho. Server might have returned non-JSON.")
    print(f"Full response text: {response.text}")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")