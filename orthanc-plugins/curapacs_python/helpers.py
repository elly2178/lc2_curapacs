import json
import base64
import requests
from curapacs_python import config

def post_data(url, data, headers=None, timeout=config.HTTP_TIMEOUT, is_json=True):
    """
    Issues http POST to a url
    """
    config.LOGGER.debug(f"post_data called with args: {url}, headers: {headers}, body with size: {len(data)}")
    if headers is None:
        headers = {}
    if config.HTTP_USER:
        headers.update(get_http_auth_header(config.HTTP_USER, config.HTTP_PASSWORD))
    if is_json:
        headers.update({"Content-Type": "application/json"})
        response = requests.post(url, json=data, headers=headers, timeout=timeout)
        try: 
            json_response = response.json()
        except json.JSONDecodeError:
            config.LOGGER.error(f"Data received by post_data is malformed json structure ({response}).")
            json_response = {}
        return json_response, response.headers
    else:
        response = requests.post(url, data=data, headers=headers, timeout=timeout)
        return response.content, response.headers

def get_data(url, headers=None, timeout=config.HTTP_TIMEOUT):
    """
    Issues http GET to a url
    """
    if not headers:
        headers = {}
    if config.HTTP_USER:
        headers.update(get_http_auth_header(config.HTTP_USER, config.HTTP_PASSWORD))
    headers.update({"Accept":"application/json"})
    response = requests.get(url, headers=headers, timeout=timeout)
    if response.status_code > 299:
        config.LOGGER.warning(f"HTTP GET got bad response, status {response.status_code}, content {response.content}")
        raise requests.ConnectionError()
    elif "Content-Type" in response.headers and "application/json" in response.headers["Content-Type"]:
        config.LOGGER.debug("HTTP GET received JSON structure.")
        return response.json(), response.headers
    else:
        config.LOGGER.info("HTTP GET received NON-JSON structure.")
        return response.content, response.headers

def get_http_auth_header(username, password):
    """
    :param username: Basic Auth Username
    :param password: Basic Auth Password
    :returns: HTTP Header as dict containing basic auth information
    """
    b64string = base64.b64encode(bytes("{}:{}".format(username, password), encoding="utf-8"))
    return {"Authorization": "Basic {}".format(b64string.decode())}
