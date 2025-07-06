# hubspot_crm.py
import requests
import json

class HubSpotCRM:
    def __init__(self, config):
        self.api_key = config['hubspot']['api_key']
        self.api_url = "https://api.hubapi.com/crm/v3/objects/contacts"

    def create_contact(self, contact_data):
        """
        Creates a contact (lead) in HubSpot CRM.
        contact_data should be a dictionary like {'firstname': 'John', 'lastname': 'Doe', 'email': 'john.doe@example.com'}
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # HubSpot requires properties to be nested under a 'properties' key
        payload = {"properties": contact_data}

        print(f"Creating HubSpot Contact with data: {contact_data}")
        try:
            response = requests.post(self.api_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            result = response.json()
            print(f"HubSpot Contact created successfully: {result.get('id')}")
            return {"success": True, "id": result.get('id')}
        except requests.exceptions.RequestException as e:
            print(f"Error creating HubSpot Contact: {e}")
            if e.response:
                print(f"Response content: {e.response.text}")
            return {"success": False, "message": str(e)}

    # You might want methods for checking existing contacts, etc.
    # For now, we focus on create_contact.

# Example usage (for testing this module independently if needed)
if __name__ == "__main__":
    # Create a dummy config (replace with your actual values for testing)
    dummy_config = {
        "hubspot": {
            "api_key": "YOUR_HUBSPOT_API_KEY_OR_PRIVATE_APP_TOKEN_HERE"
        }
    }
    # IMPORTANT: Replace dummy config with actual values from your crm_config.json for real testing
    # Or, load from the actual crm_config.json if you want to test here.
    # from config import load_config # This would be how your bot loads it
    # config = load_config() # If load_config is available

    try:
        # For testing this script directly, make sure your dummy_config has valid tokens
        hubspot_api = HubSpotCRM(dummy_config)

        # Test creating a contact
        new_contact_data = {
            "firstname": "HubSpot",
            "lastname": "Test",
            "email": "hubspot.test@example.com",
            "phone": "9988776655",
            "lead_source": "Telegram Bot" # You might need to create a custom property for this in HubSpot
        }
        # contact_creation_result = hubspot_api.create_contact(new_contact_data)
        # print("Contact Creation Result:", contact_creation_result)

    except Exception as e:
        print(f"Failed to initialize HubSpotCRM for testing: {e}")