from flask import Flask, request, render_template, url_for
import requests
import os

key = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImIxMmU2OGZiLTk1MWUtNDUwMS05MGZlLWI3ZGE4YjhkYTdjMyIsImlhdCI6MTc3NTcxOTc1OCwic3ViIjoiZGV2ZWxvcGVyL2JiMzhmY2M4LTIyMzctNmNlMC1jZmY5LTUzNzM3OGY0NGEzNiIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiNzQuMjIwLjQ4LjI0MiJdLCJ0eXBlIjoiY2xpZW50In1dfQ.xdZTigak-0FZT5HvkRk_q3fg-UrMJxze51JlEVAIHCrFWuRXAsEPSH_5lAxz-sV1XvfMj4jxgllG-HBOKNdsJg"

headers = {"Authorization": f"Bearer {key}"}
base_url = "https://api.brawlstars.com/v1/"

app = Flask(__name__, template_folder="html", static_folder="static")

# Папки для статики
ICON_PATH = "icons"
SKIN_PATH = "skins"
GADGET_PATH = "gadgets"
STAR_PATH = "starpowers"

def player_data(tag):
    tag = tag.strip("#").upper()
    resp = requests.get(f"{base_url}players/%23{tag}", headers=headers)
    data = resp.json()
    return data

def get_icon(name, folder):
    """Возвращает путь к статике, если есть, иначе None"""
    if not name:
        return None
    fname = f"{name.lower().replace(' ','_')}.png"
    path = os.path.join(app.static_folder, folder, fname)
    if os.path.isfile(path):
        return url_for('static', filename=f"{folder}/{fname}")
    return None

def prepare_brawlers(brawlers):
    """Собираем ссылки на иконки, скины, гаджеты и пассивки"""
    for b in brawlers:
        b_name = b.get("name", "")
        # иконка бойца
        b["icon_url"] = get_icon(b_name, ICON_PATH) or b_name
        # скин
        skin_name = b.get("skin", {}).get("name", "")
        b["skin_url"] = get_icon(f"{b_name}_{skin_name}", SKIN_PATH) or skin_name
        # гаджеты
        b["gadgets_url"] = [get_icon(g.get("name",""), GADGET_PATH) or g.get("name","") for g in b.get("gadgets",[])]
        # пассивки (Star Powers)
        b["star_url"] = [get_icon(s.get("name",""), STAR_PATH) or s.get("name","") for s in b.get("starPowers",[])]
    return brawlers

@app.route("/")
def main_page():
    return render_template("main.html")

@app.route("/ip")
def get_ip():
    import requests
    return requests.get("https://api.ipify.org").text

def get_icon(name, folder):
    if not name:
        return None
    fname = f"{name.lower().replace(' ','_')}.png"
    return f"https://raw.githubusercontent.com/KimaruOff/StarStats/main/static/{folder}/{fname}"

@app.route("/player")
def player_stats():
    q = request.args.get("q")
    if not q:
        return "Введите тег или ник"

    # тег или ник
    tag = q if q.startswith("#") else "#" + q
    data = player_data(tag)

    # Бойцы
    brawlers = data.get("brawlers", [])
    if not isinstance(brawlers, list):
        brawlers = []
    brawlers = prepare_brawlers(brawlers)

    # максимальный винстрик
    max_streak = 0
    max_brawler = ""
    for b in brawlers:
        streak = b.get("maxWinStreak", 0)
        if streak > max_streak:
            max_streak = streak
            max_brawler = b.get("name","")

    # общее количество бойцов
    total_brawlers = len(brawlers)

    return render_template("player.html",
                           player=data,
                           brawlers=brawlers,
                           max_streak=max_streak,
                           max_brawler=max_brawler,
                           total_brawlers=total_brawlers)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
