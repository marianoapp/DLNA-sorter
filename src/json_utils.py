import urllib.request
from urllib.error import URLError
import ssl
from socket import timeout
import json
import re
from logger import logger


def get_content(link):
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(link, headers={'User-Agent': 'Mozilla/5.0'})
        page = urllib.request.urlopen(req, timeout=5, context=ctx)
        content = page.read()
        return content
    except timeout:
        logger.error("Timeout loading %s", link)
    except URLError as e:
        logger.error("Error loading %s: %s", link, e.reason)
    except:
        logger.exception("Exception loading %s", link)


def get_json(link):
    content = get_content(link)
    if content:
        try:
            data = json.loads(content)
            return data
        except:
            logger.exception("Failure loading %s", link)


def get_json_path(root: dict, path: str):
    current = root
    value = None
    path = path.replace("[", ".[")
    path = path.replace("(", ".(")
    names = path.split(".")
    while len(names) > 0:
        if current is None:
            break
        n = names.pop(0)
        value = None
        if n[0] == "[" and n[-1] == "]":
            value = get_json_array_value(current, n)
        elif n[0] == "(" and n[-1] == ")":
            value = get_json_array_value(list(current.values()), n)
        elif n in current:
            value = current[n]
        current = value
    return value


def get_json_array_value(current, n):
    value = None
    x = n[1:-1]
    if x.isdigit():
        index = int(x)
        if index < len(current):
            value = current[index]
    else:
        matches = re.match(r"(.+)='(.+)'", x, re.IGNORECASE)
        if matches:
            prop_name = matches[1]
            prop_value = matches[2]
            for item in current:
                if str(item[prop_name]).casefold() == prop_value.casefold():
                    value = item
                    break
    return value

