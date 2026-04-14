"""Download OpenCV Facemark LBF model (~54 MB) if missing."""
from __future__ import annotations

import os
import ssl
import urllib.request

LBF_URL = (
    "https://raw.githubusercontent.com/kurnianggoro/GSOC2017/master/data/lbfmodel.yaml"
)
TARGET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lbfmodel.yaml")


def main():
    if os.path.isfile(TARGET):
        print(f"Already present: {TARGET}")
        return
    print(f"Downloading {LBF_URL} ...")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
    opener.addheaders = [("User-Agent", "Mozilla/5.0")]
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(LBF_URL, TARGET)
    print(f"Saved to {TARGET}")


if __name__ == "__main__":
    main()
