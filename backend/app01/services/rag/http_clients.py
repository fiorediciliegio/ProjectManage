import requests
from openai import DefaultHttpxClient


def build_no_proxy_openai_http_client():
    return DefaultHttpxClient(trust_env=False)


def build_no_proxy_requests_session():
    session = requests.Session()
    session.trust_env = False
    return session
