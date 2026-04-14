import os
import urllib.request
import ssl

icons = {
    "Dizziness": "tornado"
}

os.makedirs("icons", exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')]
urllib.request.install_opener(opener)

for name, icon_name in icons.items():
    url = f"https://img.icons8.com/color/96/000000/{icon_name}.png"
    safe_name = name.replace("'", "").replace(" ", "_").lower()
    path = os.path.join("icons", f"{safe_name}.png")
    
    print(f"Downloading {name}...")
    try:
        urllib.request.urlretrieve(url, path)
        print(f"Successfully downloaded {name}")
    except Exception as e:
        print(f"Error downloading {name}: {e}")

print("Done.")
