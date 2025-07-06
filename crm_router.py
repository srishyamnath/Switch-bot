# crm_router.py
from zoho_crm import ZohoCRM
from hubspot_crm import HubSpotCRM
import json

def load_config(file_path='config/crm_config.json'):
    """Loads the CRM configuration from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Config file not found at {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}. Check file format.")
        return None

class CRMRouter:
    def __init__(self):
        self.config = load_config()
        if not self.config:
            raise Exception("Failed to load CRM configuration. Please check config/crm_config.json")

        self.selected_crm = self.config.get('crm', 'zoho') # Default to zoho
        self.crm_client = None
        self._initialize_crm_client()

    def _initialize_crm_client(self):
        if self.selected_crm == 'zoho':
            print("Initializing Zoho CRM client...")
            self.crm_client = ZohoCRM(self.config)
        elif self.selected_crm == 'hubspot':
            print("Initializing HubSpot CRM client...")
            self.crm_client = HubSpotCRM(self.config)
        else:
            raise ValueError(f"Unsupported CRM specified in config: {self.selected_crm}")

    def create_lead_or_contact(self, data):
        """
        Routes the lead/contact creation request to the appropriate CRM.
        'data' should be a dictionary containing fields common to both CRMs,
        which will be mapped internally.
        """
        if not self.crm_client:
            raise Exception("CRM client not initialized.")

        print(f"Attempting to create entry in {self.selected_crm}...")

        if self.selected_crm == 'zoho':
            # Map generic data to Zoho's Lead module fields
            zoho_lead_data = {
                "Company": data.get("company", "N/A"), # Default company
                "Last_Name": data.get("last_name", "Unknown"),
                "First_Name": data.get("first_name", "Lead"),
                "Email": data.get("email"),
                "Phone": data.get("phone"),
                "Lead_Source": data.get("lead_source", "Telegram Bot")
            }
            if not zoho_lead_data["Email"] and not zoho_lead_data["Phone"]:
                print("Warning: Email and Phone are missing for Zoho Lead. Zoho might require at least one for quality leads.")
                # You might want to handle this more robustly, e.g., return an error or prompt user

            return self.crm_client.create_lead(zoho_lead_data)

        elif self.selected_crm == 'hubspot':
            # Map generic data to HubSpot's Contact properties
            hubspot_contact_data = {
                "firstname": data.get("first_name"),
                "lastname": data.get("last_name"),
                "email": data.get("email"),
                "phone": data.get("phone"),
                "company": data.get("company"),
                "lead_source": data.get("lead_source", "Telegram Bot") # Ensure you have a 'lead_source' custom property in HubSpot
            }
            # Remove None values for HubSpot
            hubspot_contact_data = {k: v for k, v in hubspot_contact_data.items() if v is not None}

            if not hubspot_contact_data.get("email") and not hubspot_contact_data.get("phone"):
                print("Warning: Email and Phone are missing for HubSpot Contact. HubSpot might require at least one for quality contacts.")
                # You might want to handle this more robustly

            return self.crm_client.create_contact(hubspot_contact_data)
        else:
            return {"success": False, "message": f"CRM '{self.selected_crm}' not supported."}


# Example Usage:
if __name__ == "__main__":
    try:
        router = CRMRouter()
        print(f"CRM configured: {router.selected_crm}")

        # Example data from lead_parser
        sample_lead_data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@example.com",
            "phone": "9876543210",
            "company": "Example Co.",
            "lead_source": "Telegram"
        }

        # result = router.create_lead_or_contact(sample_lead_data)
        # print("CRM Operation Result:", result)

    except Exception as e:
        print(f"Error initializing or using CRMRouter: {e}")