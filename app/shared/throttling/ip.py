from fastapi import Request, HTTPException

def get_ip(request: Request):
    return request.client.host
    
def get_user_id(request:Request):
    return request.headers.get("user-id")