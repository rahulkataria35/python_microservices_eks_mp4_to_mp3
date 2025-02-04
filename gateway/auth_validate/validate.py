import os
import requests

def token(request):
    if not "Authorization" in request.headers:
        return None, ("Missing Credentials", 401)
    
    token = request.headers["Authorization"]

    if not token:
        return None, ("Missing Credentials", 401)
    
    url = f"{os.environ.get('AUTH_SVC_ADDRESS','127.0.0.1:5000')}/validate"
    
    response = requests.post(
        url,
        headers={"Authorization": token}
    )

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)