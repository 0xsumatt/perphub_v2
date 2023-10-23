import httpx


def color_green(val):
    return 'color: green'
def color_red(val):
    return 'color: red'

def fetch_aevo_assets():
    symbols = httpx.get("https://api.aevo.xyz/assets").json()
    return symbols