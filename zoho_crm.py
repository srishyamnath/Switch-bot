# zoho_crm.py
import requests
import json
import time

class ZohoCRM:
    def __init__(self, config):
        self.client_id = config['zoho']['client_id']
        self.client_secret = config['zoho']['client_secret']
        self.refresh_token = config['zoho']['refresh_token']
        self.redirect_uri = config['zoho']['redirect_uri']
        self.access_token = None
        self.token_expires_at = 0 # Unix timestamp
        self.accounts_url = config['zoho'].get('accounts_url', "https://accounts.zoho.in/oauth/v2/token")
        self.api_url = config['zoho'].get('api_url', "https://www.zohoapis.in/crm/v6/") # Use v6 for latest API

        self._load_tokens_from_file() # Try to load existing tokens if available
        self._ensure_access_token() # Ensure we have a valid access token on startup

    def _get_token_file_path(self):
        # A simple way to store tokens locally, relative to the script
        return 'zoho_tokens.json'

    def _load_tokens_from_file(self):
        try:
            with open(self._get_token_file_path(), 'r') as f:
                data = json.load(f)
                self.access_token = data.get('access_token')
                self.refresh_token = data.get('refresh_token') # Ensure refresh token is up-to-date
                self.token_expires_at = data.get('token_expires_at', 0)
                print("Zoho tokens loaded from file.")
        except FileNotFoundError:
            print("No existing Zoho token file found.")
        except json.JSONDecodeError:
            print("Error decoding Zoho token file. Starting fresh.")
        except Exception as e:
            print(f"Error loading Zoho tokens: {e}")

    def _save_tokens_to_file(self):
        data = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_expires_at': self.token_expires_at
        }
        try:
            with open(self._get_token_file_path(), 'w') as f:
                json.dump(data, f, indent=4)
                print("Zoho tokens saved to file.")
        except Exception as e:
            print(f"Error saving Zoho tokens: {e}")


    def _refresh_access_token(self):
        print("Refreshing Zoho access token...")
        params = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "redirect_uri": self.redirect_uri # Required even for refresh_token grant type
        }
        try:
            response = requests.post(self.accounts_url, params=params)
            response.raise_for_status()
            data = response.json()
            if "access_token" in data:
                self.access_token = data["access_token"]
                # Expires_in is in seconds, typically 3600 (1 hour)
                self.token_expires_at = time.time() + data.get("expires_in", 3600) - 300 # Subtract 5 mins buffer
                print("Zoho access token refreshed successfully.")
                self._save_tokens_to_file()
                return True
            else:
                print("Failed to get new access token during refresh.")
                print(f"Response: {data}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Error refreshing Zoho access token: {e}")
            if e.response:
                print(f"Response content: {e.response.text}")
            return False

    def _ensure_access_token(self):
        if not self.access_token or time.time() >= self.token_expires_at:
            if not self._refresh_access_token():
                raise Exception("Failed to obtain a valid Zoho Access Token.")
        return self.access_token

    def create_lead(self, lead_data):
        """Creates a lead in Zoho CRM."""
        self._ensure_access_token()
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.access_token}",
            "Content-Type": "application/json"
        }
        # Zoho expects data in 'data' array
        payload = {"data": [lead_data]}
        url = f"{self.api_url}Leads"

        print(f"Creating Zoho Lead with data: {lead_data}")
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()
            if result and result.get("data") and result["data"][0].get("code") == "SUCCESS":
                print(f"Zoho Lead created successfully: {result['data'][0]['details']['id']}")
                return {"success": True, "id": result['data'][0]['details']['id']}
            else:
                print(f"Failed to create Zoho Lead. Response: {result}")
                return {"success": False, "message": result.get("data", [{}])[0].get("message", "Unknown error")}
        except requests.exceptions.RequestException as e:
            print(f"Error creating Zoho Lead: {e}")
            if e.response:
                print(f"Response content: {e.response.text}")
            return {"success": False, "message": str(e)}

    # You might want methods for creating contacts, checking existing leads, etc.
    # For now, we focus on create_lead.

# Example usage (for testing this module independently if needed)
if __name__ == "__main__":
    # Create a dummy config (replace with your actual values for testing)
    dummy_config = {
        "zoho": {
            "client_id": "YOUR_ZOHO_CLIENT_ID_HERE",
            "client_secret": "YOUR_ZOHO_CLIENT_SECRET_HERE",
            "refresh_token": "YOUR_ZOHO_REFRESH_TOKEN_HERE",
            "redirect_uri": "https://www.zoho.in",
            "accounts_url": "https://accounts.zoho.in/oauth/v2/token",
            "api_url": "https://www.zohoapis.in/crm/v6/"
        }
    }
    # IMPORTANT: Replace dummy config with actual values from your crm_config.json for real testing
    # Or, load from the actual crm_config.json if you want to test here.
    # from config import load_config # This would be how your bot loads it
    # config = load_config() # If load_config is available

    try:
        # For testing this script directly, make sure your dummy_config has valid tokens
        zoho_api = ZohoCRM(dummy_config)
        
        # Test creating a lead
        new_lead_data = {
            "Company": "Test Company",
            "Last_Name": "Bot",
            "First_Name": "Telegram",
            "Email": "telegram.bot@example.com",
            "Phone": "9876543210",
            "Lead_Source": "Telegram Bot"
        }
        # lead_creation_result = zoho_api.create_lead(new_lead_data)
        # print("Lead Creation Result:", lead_creation_result)

    except Exception as e:
        print(f"Failed to initialize ZohoCRM for testing: {e}")