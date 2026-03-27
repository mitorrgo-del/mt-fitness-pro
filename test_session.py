from instagrapi import Client
cl = Client()
sid = "41956480253%3AZ8lRbflfJJ6Ztp%3A28%3AAYg8VzOLkXMIye48OTbmrGeQqRRKczF7cl0lKlq7cw"
try:
    cl.login_by_sessionid(sid)
    print(f"LOGIN OK: {cl.user_info_by_username('mtfitnesspro_oficial').username}")
except Exception as e:
    print(f"LOGIN FAIL: {e}")
