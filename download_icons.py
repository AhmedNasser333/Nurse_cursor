import os
import urllib.request

icons = {
    "Emergency": "alert-box",
    "Pain": "emoticon-sick-outline",
    "Airway Obstruction": "lungs",
    "Suction": "vacuum",
    "Care": "heart-pulse",
    "Water": "water",
    "Food": "food",
    "Dizziness": "head-alert",
    "Can't Sleep": "bed-outline",
    "Change Position": "seat-recline-normal",
    "Right": "arrow-right-bold",
    "Left": "arrow-left-bold",
    "Back": "arrow-down-bold"
}

os.makedirs("icons", exist_ok=True)

for name, icon_name in icons.items():
    url = f"https://api.iconify.design/mdi/{icon_name}.png?color=black&width=80&height=80"
    safe_name = name.replace("'", "").replace(" ", "_").lower()
    path = os.path.join("icons", f"{safe_name}.png")
    if not os.path.exists(path):
        print(f"Downloading {name}...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(path, 'wb') as out_file:
                out_file.write(response.read())
        except Exception as e:
            print(f"Error downloading {name}: {e}")
print("Done.")
