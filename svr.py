from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__, template_folder="html", static_folder="static")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///player_history.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# === Модели базы ===
class Player(db.Model):
    tag = db.Column(db.String, primary_key=True)
    latest_name = db.Column(db.String, nullable=False)
    nicks = db.relationship('NickHistory', backref='player', lazy=True, cascade="all, delete-orphan")

class NickHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String, db.ForeignKey('player.tag'), nullable=False)
    name = db.Column(db.String, nullable=False)
    __table_args__ = (db.UniqueConstraint('tag', 'name', name='_tag_name_uc'),)

db.create_all()

# === Конфиг API ===
key = ""eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjI1ODAxMjk5LTY3ZTQtNDFkNS04MzM5LTg3OTAzMzViMzFjMCIsImlhdCI6MTc3NTcyMTkyMCwic3ViIjoiZGV2ZWxvcGVyL2JiMzhmY2M4LTIyMzctNmNlMC1jZmY5LTUzNzM3OGY0NGEzNiIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiNzQuMjIwLjQ4LjI0MiIsIjkxLjIyNS4xNjIuNjEiXSwidHlwZSI6ImNsaWVudCJ9XX0.IH82igKjBy7w_WvK9xDiqISPXLlem-NCcAjfXCaqyklXG8dMF3YN5YED1F0b2NCIUFyJ4Ri4LvcProzMwauAXw""
headers = {"Authorization": f"Bearer {key}"}
base_url = "https://api.brawlstars.com/v1/"

# === Папки для статики на GitHub ===
ICON_PATH = "icons"
SKIN_PATH = "skins"
GADGET_PATH = "gadgets"
STAR_PATH = "starpowers"

def gh_icon(name, folder):
    if not name:
        return None
    fname = f"{name.lower().replace(' ','_')}.png"
    return f"https://raw.githubusercontent.com/KimaruOff/StarStats/refs/heads/main/static/{folder}/{fname}"

def player_data(tag):
    tag = tag.strip("#").upper()
    resp = requests.get(f"{base_url}players/%23{tag}", headers=headers)
    return resp.json()

def prepare_brawlers(brawlers):
    for b in brawlers:
        b_name = b.get("name","")
        skin_name = b.get("skin", {}).get("name","")
        
        b["icon_url"] = gh_icon(b_name, ICON_PATH)
        b["skin_url"] = gh_icon(f"{b_name}_{skin_name}", SKIN_PATH) if skin_name else None
        b["gadgets"] = [(gh_icon(g.get("name",""), GADGET_PATH), g) for g in b.get("gadgets",[])]
        b["starPowers"] = [(gh_icon(s.get("name",""), STAR_PATH), s) for s in b.get("starPowers",[])]
    return brawlers

# === Работа с историей ===
def save_player(tag, name):
    player = Player.query.get(tag)
    if player:
        player.latest_name = name
    else:
        player = Player(tag=tag, latest_name=name)
        db.session.add(player)
    # Добавляем ник в историю, если нет
    if not NickHistory.query.filter_by(tag=tag, name=name).first():
        db.session.add(NickHistory(tag=tag, name=name))
    db.session.commit()

def find_tag_by_nick(nick):
    nh = NickHistory.query.filter_by(name=nick).first()
    if nh:
        return nh.tag
    return None

# === Роуты ===
@app.route("/")
def main_page():
    return render_template("main.html")

@app.route("/player")
def player_stats():
    q = request.args.get("q")
    if not q:
        return "Введите тег или ник"

    # Определяем тег
    if q.startswith("#"):
        tag = q.upper()
    else:
        tag = find_tag_by_nick(q)
        if not tag:
            return f"Ник {q} не найден в истории. Попробуйте тег."

    # Получаем данные через API
    data = player_data(tag.strip("#"))

    # Сохраняем тег и ник
    save_player(tag, data.get("name","Unknown"))

    # Бойцы
    brawlers = data.get("brawlers", [])
    if not isinstance(brawlers, list):
        brawlers = []
    brawlers = prepare_brawlers(brawlers)

    # Максимальный винстрик
    max_streak = 0
    max_brawler = ""
    for b in brawlers:
        streak = b.get("maxWinStreak", 0)
        if streak > max_streak:
            max_streak = streak
            max_brawler = b.get("name","")
    max_brawler_icon = gh_icon(max_brawler, ICON_PATH) if max_brawler else None

    total_brawlers = len(brawlers)

    return render_template("player.html",
                           player=data,
                           brawlers=brawlers,
                           max_streak=max_streak,
                           max_brawler=max_brawler,
                           max_brawler_icon=max_brawler_icon,
                           total_brawlers=total_brawlers)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
