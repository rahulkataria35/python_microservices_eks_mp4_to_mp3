import os
import requests
from logger import get_logger

# Get logger instance
logger = get_logger(__name__)

def login(request):
    """
    Authenticates a user by forwarding their credentials to an authentication service.
    """
    # Extract the JSON payload from the request
    try:
        credentials = request.get_json()
    except Exception as e:
        return None, ("Invalid JSON format", 400)

    # Validate required fields in the credentials
    if not credentials or not all(k in credentials for k in ["username", "password", "email"]):
        return None, ("Missing required fields: 'username', 'password', or 'email'", 400)

    # Prepare the authentication service endpoint
    auth_service_address = os.environ.get("AUTH_SVC_ADDRESS","127.0.0.1:5000")
    if not auth_service_address:
        return None, ("Authentication service address not configured", 500)

    url = f"{auth_service_address}/login"
    
    try:
        # Send a POST request to the authentication service with the JSON payload
        response = requests.post(url, json=credentials)

        # Check for successful authentication
        if response.status_code == 200:
            return response.text, None  # Return the token on success

        # Handle authentication failure
        return None, (response.json().get("error", "Authentication failed"), response.status_code)

    except requests.exceptions.ConnectionError:
        return None, ("Failed to connect to the authentication service", 500)
    except requests.exceptions.Timeout:
        return None, ("Authentication service request timed out", 504)
    except requests.exceptions.RequestException as e:
        return None, (f"Unexpected error: {str(e)}", 500)