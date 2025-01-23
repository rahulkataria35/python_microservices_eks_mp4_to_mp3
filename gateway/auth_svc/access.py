import os
import requests

def login(request):
    """
    Authenticates a user by forwarding their credentials to an authentication service.
    """
    auth = request.authorization  # Extract the Authorization header from the request

    if not auth:
        return None, ("Missing credentials", 401)

    # Prepare Basic Authentication tuple (username, password)
    basicAuth = (auth.username, auth.password)

    # Send a POST request to the authentication service for user login
    try:
        response = requests.post(
            f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/login",
            auth=basicAuth
        )
    except requests.exceptions.RequestException as e:
        return None, (f"Authentication service error: {str(e)}", 500)

    if response.status_code == 200:
        return response.text, None  # Return the authentication token

    # If authentication fails, return the error message and status code from the service
    else:
        return None, (response.text, response.status_code)
