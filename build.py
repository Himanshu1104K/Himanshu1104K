"""Renders the profile README cards as SVGs (dark + light). Stdlib only: `python build.py`."""
import base64
import json
import textwrap
import urllib.request
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "assets"
LEETCODE_USER = "himanshu1104k"
# Used when LeetCode is unreachable, so a failed fetch never blanks the card.
LEETCODE_FALLBACK = {"All": (577, 4087), "Easy": (335, 972), "Medium": (228, 2131), "Hard": (14, 984), "rank": 158691}

W = 880
SANS = "Inter,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

THEMES = {
    "light": dict(card="#FBFBF8", inset="#F2F2EC", line="#E3E3DC", text="#131316", muted="#5F606A",
                  faint="#A2A3AB", dots="#E6E6DF", accent="#4D7C0F", ink="#FFFFFF",
                  easy="#16A34A", medium="#D97706", hard="#DC2626"),
}

METRICS = [
    ("1.5", "yrs", "Production experience", "Python and Go services"),
    ("5", "+", "Microservices owned", "at Bump.fm"),
    (None, "", "LeetCode problems", "solved in Java"),  # filled from the API
    ("20k", "+", "Developer community", "GDG on Campus MIET"),
    ("35", "%", "Throughput gain", "with async Redis pipelines"),
    ("1k", "+", "Concurrent requests", "quick-commerce backend"),
]

STACK = [
    ("Languages", ["Python*", "Go*", "Java"]),
    ("Backend", ["FastAPI*", "GraphQL", "REST", "SQLAlchemy 2", "Alembic", "WebSockets", "Kafka", "RabbitMQ"]),
    ("AI and LLMs", ["LangGraph*", "LangChain", "RAG", "Qdrant", "ChromaDB", "Neo4j"]),
    ("Data", ["PostgreSQL*", "PostGIS", "TimescaleDB", "MySQL", "Redis"]),
    ("Infra", ["Docker", "AWS S3", "Azure Blob", "GCP", "GitHub Actions", "Nginx"]),
]

EXPERIENCE = [
    ("APR 2025 — NOW", True, "Bump.fm", "Core backend engineer · Persist Ventures", [
        "Own 5+ Python and Go microservices behind the REST and GraphQL APIs: auth, upload, playback, playlists, discovery and leaderboards.",
        "Own the music-system layer: distribution, DSP data sharing, play logging, impression calculation and analytics.",
        "Solana token launches, AMM trading and claims, with Privy wallets and MoonPay on-ramps.",
    ]),
    ("2025", False, "Hey Ova", "AI voice assistant · Persist Ventures", [
        "LangGraph workflow with intent routing, RAG on Qdrant and tool-calling agents for Calendar, Gmail and search.",
        "Three-store memory: Postgres for facts, Neo4j for relationships, Qdrant for semantic recall.",
    ]),
    ("2025", False, "MEND", "Real-time conflict mediation · Persist Ventures", [
        "FastAPI REST and WebSocket backend with a 3-stage LangGraph pipeline and live streaming.",
        "Raised throughput 35% with async Redis pipelines.",
    ]),
    ("OCT 2025 — NOW", True, "Freelance", "Commerce and marketplace backends", [
        "Quick-commerce: PostGIS delivery matching and a RabbitMQ order queue at 1,000+ concurrent requests.",
        "OOH ad marketplace: GiST exclusion constraints guarantee zero double-bookings.",
        "Dairy quick-commerce: FastAPI backend, in progress.",
    ]),
]

LINKS = [
    ("email", "Email me", True),
    ("linkedin", "LinkedIn", False),
    ("leetcode", "LeetCode", False),
]


def tw(s, size, mono=False):
    """Rough text width; good enough for laying out chips and pills."""
    return len(s) * size * (0.61 if mono else 0.56)


def svg(t, h, body, w=W, rx=18, defs=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none">
<style>
text{{font-family:{SANS};fill:{t['text']}}}
.mono{{font-family:{MONO};font-size:11px;letter-spacing:.14em;fill:{t['muted']}}}
.muted{{fill:{t['muted']}}} .faint{{fill:{t['faint']}}} .acc{{fill:{t['accent']}}}
.up{{animation:up .8s cubic-bezier(.2,.7,.2,1) both}}
.flow{{stroke-dasharray:3 7;animation:flow 1.4s linear infinite}}
.pulse{{transform-box:fill-box;transform-origin:center;animation:pulse 2s ease-out infinite}}
.grow{{transform-box:fill-box;transform-origin:left;animation:grow 1.2s cubic-bezier(.2,.7,.2,1) both}}
@keyframes up{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}
@keyframes flow{{to{{stroke-dashoffset:-20}}}}
@keyframes pulse{{from{{opacity:.7;transform:scale(1)}}to{{opacity:0;transform:scale(3.2)}}}}
@keyframes grow{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<defs>
<clipPath id="card"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>
<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="{t['dots']}"/></pattern>
{defs}
</defs>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="{t['card']}" stroke="{t['line']}"/>
{body}
</svg>"""


def label(x, y, s, anchor="start"):
    return f'<text x="{x}" y="{y}" class="mono" text-anchor="{anchor}">{escape(s.upper())}</text>'


def delay(i):
    return f'style="animation-delay:{i * 0.07:.2f}s"'


def hero(t):
    def node(cx, cy, w, text, hot=False):
        stroke = t["accent"] if hot else t["line"]
        return (f'<rect x="{cx - w / 2}" y="{cy - 17}" width="{w}" height="34" rx="9" fill="{t["inset"]}" stroke="{stroke}"/>'
                f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" font-family="{MONO}" font-size="12" class="{"acc" if hot else "muted"}">{text}</text>')

    def edge(x1, y1, x2, y2):
        mid = (y1 + y2) / 2
        d = f"M{x1} {y1} C{x1} {mid},{x2} {mid},{x2} {y2}"
        return (f'<path d="{d}" stroke="{t["line"]}" stroke-width="1.5"/>'
                f'<path d="{d}" stroke="{t["accent"]}" stroke-width="1.5" class="flow"/>')

    status = "Now - core backend engineer at Bump.fm"
    pill_w = tw(status, 13) + 52
    body = f"""
<g clip-path="url(#card)">
  <rect width="{W}" height="340" fill="url(#dots)"/>
  <circle cx="720" cy="40" r="300" fill="url(#glow)"/>
</g>
<g class="up">{label(48, 66, "Backend engineer · Meerut, India")}</g>
<text x="46" y="134" font-size="60" font-weight="700" letter-spacing="-2" class="up" {delay(1)}>Himanshu Kumar</text>
<g class="up" {delay(2)}>
  <text x="48" y="178" font-size="17" class="muted">I build the backend systems behind music,</text>
  <text x="48" y="203" font-size="17" class="muted">AI and commerce products, in Python, FastAPI and Go.</text>
</g>
<g class="up" {delay(3)}>
  <rect x="48" y="244" width="{pill_w}" height="38" rx="19" fill="{t['inset']}" stroke="{t['line']}"/>
  <circle cx="70" cy="263" r="4" fill="{t['accent']}" class="pulse"/>
  <circle cx="70" cy="263" r="4" fill="{t['accent']}"/>
  <text x="84" y="268" font-size="13" font-weight="500">{escape(status)}</text>
</g>
<g class="up" {delay(4)}>
  {edge(700, 95, 700, 143)}
  {edge(700, 177, 600, 233)}{edge(700, 177, 700, 233)}{edge(700, 177, 800, 233)}
  {node(700, 78, 110, "clients")}
  {node(700, 160, 168, "FastAPI · Go", hot=True)}
  {node(600, 250, 100, "Postgres")}{node(700, 250, 80, "Redis")}{node(800, 250, 80, "Kafka")}
  <text x="700" y="304" text-anchor="middle" font-family="{MONO}" font-size="10" letter-spacing="1.4" class="faint">THE SHAPE OF MOST THINGS I BUILD</text>
</g>"""
    glow = (f'<radialGradient id="glow"><stop offset="0" stop-color="{t["accent"]}" stop-opacity=".16"/>'
            f'<stop offset="1" stop-color="{t["accent"]}" stop-opacity="0"/></radialGradient>')
    return svg(t, 340, body, defs=glow)


def metrics(t, solved):
    rows = [(str(solved) if v is None else v, *rest) for v, *rest in METRICS]
    col, top, row_h = 800 / 3, 74, 112
    parts = [label(40, 46, "By the numbers")]
    for i, (num, unit, name, note) in enumerate(rows):
        x, y = 40 + (i % 3) * col + (0 if i % 3 == 0 else 28), top + (i // 3) * row_h
        parts.append(f"""<g class="up" {delay(i)}>
  <text x="{x}" y="{y + 42}" font-size="40" font-weight="700" letter-spacing="-1.5">{num}<tspan class="acc" font-size="24" dx="2">{unit}</tspan></text>
  <text x="{x}" y="{y + 66}" font-size="14" font-weight="500">{name}</text>
  <text x="{x}" y="{y + 85}" font-size="12" class="faint">{note}</text>
</g>""")
    for c in (1, 2):
        parts.append(f'<line x1="{40 + c * col}" y1="{top + 4}" x2="{40 + c * col}" y2="{top + 2 * row_h - 4}" stroke="{t["line"]}"/>')
    parts.append(f'<line x1="40" y1="{top + row_h - 6}" x2="840" y2="{top + row_h - 6}" stroke="{t["line"]}"/>')
    return svg(t, top + 2 * row_h + 10, "\n".join(parts))


def leetcode(t, lc):
    solved, total = lc["All"]
    x0, bar_w, gap = 340, 500, 4
    parts = [
        label(40, 46, "LeetCode"),
        label(840, 46, "Synced daily", anchor="end"),
        f'<text x="38" y="136" font-size="76" font-weight="700" letter-spacing="-3" class="up">{solved}</text>',
        f'<text x="40" y="166" font-size="14" class="muted up" {delay(1)}>problems solved of {total:,}</text>',
        f'<text x="40" y="190" font-size="13" class="faint up" {delay(2)}>Global rank #{lc["rank"]:,}</text>',
        f'<rect x="{x0}" y="88" width="{bar_w}" height="10" rx="5" fill="{t["inset"]}"/>',
    ]
    x = x0
    levels = ["Easy", "Medium", "Hard"]
    for i, lvl in enumerate(levels):
        n, of = lc[lvl]
        w = max(6, (bar_w - gap * 2) * n / solved)
        parts.append(f'<rect x="{x:.1f}" y="88" width="{w:.1f}" height="10" rx="5" fill="{t[lvl.lower()]}" class="grow" {delay(i + 2)}/>')
        x += w + gap
        cx = x0 + i * 180
        parts.append(f"""<g class="up" {delay(i + 3)}>
  <circle cx="{cx + 4}" cy="137" r="4" fill="{t[lvl.lower()]}"/>
  <text x="{cx + 16}" y="141" font-size="13" class="muted">{lvl}</text>
  <text x="{cx}" y="176" font-size="28" font-weight="650" letter-spacing="-1">{n}<tspan font-size="13" font-weight="400" class="faint" dx="4">/ {of:,}</tspan></text>
  <text x="{cx}" y="198" font-size="12" class="faint">{n / of:.0%} of all {lvl.lower()}</text>
</g>""")
    return svg(t, 230, "\n".join(parts))


def stack(t):
    parts, y = [label(40, 46, "Toolbox")], 80
    for gi, (group, items) in enumerate(STACK):
        if gi:
            parts.append(f'<line x1="40" y1="{y - 14}" x2="840" y2="{y - 14}" stroke="{t["line"]}"/>')
        parts.append(f'<text x="40" y="{y + 20}" font-size="13" font-weight="500" class="muted">{escape(group)}</text>')
        x = 200
        for item in items:
            hot = item.endswith("*")
            name = item.rstrip("*")
            w = tw(name, 13) + (44 if hot else 30)
            if x + w > 840:
                x, y = 200, y + 40
            fill, stroke = (t["inset"], t["accent"]) if hot else (t["inset"], t["line"])
            dot = f'<circle cx="{x + 15}" cy="{y + 15}" r="3" fill="{t["accent"]}"/>' if hot else ""
            parts.append(f'<g class="up" {delay(gi)}><rect x="{x}" y="{y}" width="{w:.0f}" height="30" rx="15" fill="{fill}" stroke="{stroke}"/>{dot}'
                         f'<text x="{x + (26 if hot else 15)}" y="{y + 20}" font-size="13" font-weight="500">{escape(name)}</text></g>')
            x += w + 8
        y += 58
    return svg(t, y, "\n".join(parts))


def experience(t):
    parts, y = [label(40, 46, "Experience")], 88
    line_top = y - 6
    for i, (when, current, org, role, points) in enumerate(EXPERIENCE):
        dot = (f'<circle cx="210" cy="{y - 5}" r="5" fill="{t["accent"]}"/>' if current
               else f'<circle cx="210" cy="{y - 5}" r="4.5" fill="{t["card"]}" stroke="{t["faint"]}" stroke-width="1.5"/>')
        block = [
            f'<text x="40" y="{y}" font-family="{MONO}" font-size="11" letter-spacing="1" class="{"acc" if current else "faint"}">{when}</text>',
            dot,
            f'<text x="236" y="{y + 1}" font-size="18" font-weight="650" letter-spacing="-.3">{escape(org)}</text>',
            f'<text x="236" y="{y + 23}" font-size="13" class="muted">{escape(role)}</text>',
        ]
        y += 52
        for p in points:
            lines = textwrap.wrap(p, 74)
            block.append(f'<rect x="236" y="{y - 8}" width="6" height="2" fill="{t["faint"]}"/>')
            for ln in lines:
                block.append(f'<text x="252" y="{y}" font-size="14" class="muted">{escape(ln)}</text>')
                y += 21
            y += 6
        parts.append(f'<g class="up" {delay(i)}>{"".join(block)}</g>')
        y += 30
    parts.insert(1, f'<line x1="210" y1="{line_top}" x2="210" y2="{y - 70}" stroke="{t["line"]}" stroke-width="1.5"/>')
    return svg(t, y - 24, "\n".join(parts))


def extras(t):
    wins = [("GATE 2025", "Qualified in Data Science and AI"),
            ("1st runner-up", "Fetchathon 2.0"),
            ("3rd runner-up", "Code-Genesis")]
    parts = [
        label(40, 46, "Community"),
        f'<text x="40" y="88" font-size="18" font-weight="650" class="up">GDG on Campus MIET</text>',
        f'<text x="40" y="112" font-size="14" class="muted up">Organizer and Community Lead · Aug 2025 - now</text>',
        f'<text x="40" y="162" font-size="34" font-weight="700" letter-spacing="-1" class="up" {delay(1)}>20,000<tspan class="acc">+</tspan><tspan font-size="13" font-weight="400" class="faint" dx="8">developers</tspan></text>',
        f'<text x="40" y="190" font-size="12" class="faint up" {delay(2)}>Co-Lead 2024 - 25 · 10+ workshops and hackathons</text>',
        f'<line x1="440" y1="40" x2="440" y2="196" stroke="{t["line"]}"/>',
        label(472, 46, "Wins"),
    ]
    for i, (head, sub) in enumerate(wins):
        y = 92 + i * 44
        parts.append(f'<g class="up" {delay(i + 1)}><text x="472" y="{y}" font-size="15" font-weight="600">{head}</text>'
                     f'<text x="600" y="{y}" font-size="14" class="muted">{sub}</text></g>')
    return svg(t, 226, "\n".join(parts))


def meme(t):
    img = base64.b64encode((OUT / "meme.png").read_bytes()).decode()
    wx, wy, ww, wh = 470, 36, 370, 360
    body = f"""
<g clip-path="url(#card)"><rect width="{W}" height="432" fill="url(#dots)"/></g>
<g class="up">{label(40, 66, "Live footage")}</g>
<g class="up" {delay(1)}>
  <text x="38" y="124" font-size="34" font-weight="700" letter-spacing="-1">Me, shipping a hotfix</text>
  <text x="38" y="166" font-size="34" font-weight="700" letter-spacing="-1">at 4:59 pm <tspan class="acc">on a Friday.</tspan></text>
</g>
<g class="up" {delay(2)}>
  <text x="40" y="214" font-size="15" class="muted">Tests: vibes. Coverage: emotional.</text>
  <text x="40" y="238" font-size="15" class="muted">Rollback plan: also vibes.</text>
</g>
<g class="up" {delay(3)} font-family="{MONO}" font-size="12">
  <rect x="40" y="300" width="380" height="76" rx="10" fill="{t['inset']}" stroke="{t['line']}"/>
  <text x="58" y="328" class="faint">$ git push origin main --force</text>
  <circle cx="62" cy="352" r="3.5" fill="{t['accent']}" class="pulse"/><circle cx="62" cy="352" r="3.5" fill="{t['accent']}"/>
  <text x="74" y="356" class="acc">deploying… please don't look at the logs</text>
</g>
<g class="up" {delay(2)}>
  <rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" rx="12" fill="{t['inset']}" stroke="{t['line']}"/>
  <circle cx="{wx + 18}" cy="{wy + 16}" r="5" fill="#FF5F57"/><circle cx="{wx + 34}" cy="{wy + 16}" r="5" fill="#FEBC2E"/><circle cx="{wx + 50}" cy="{wy + 16}" r="5" fill="#28C840"/>
  <text x="{wx + ww / 2}" y="{wy + 20}" text-anchor="middle" font-family="{MONO}" font-size="11" class="faint">prod_deploy.png</text>
  <image x="{wx + 1}" y="{wy + 32}" width="{ww - 2}" height="{wh - 33}" preserveAspectRatio="xMidYMid slice" clip-path="url(#shot)" href="data:image/png;base64,{img}"/>
</g>
<g transform="rotate(-7 {wx + 6} {wy + wh - 22})" class="up" {delay(5)}>
  <rect x="{wx - 40}" y="{wy + wh - 40}" width="196" height="36" rx="8" fill="{t['accent']}"/>
  <text x="{wx + 58}" y="{wy + wh - 17}" text-anchor="middle" font-size="13" font-weight="700" fill="{t['ink']}" style="fill:{t['ink']}">it works on my machine</text>
</g>"""
    shot = f'<clipPath id="shot"><rect x="{wx + 1}" y="{wy + 32}" width="{ww - 2}" height="{wh - 33}" rx="11"/></clipPath>'
    return svg(t, 432, body, defs=shot)


def button(t, text, primary):
    w = tw(text, 14) + 62
    fill, stroke, ink = (t["accent"], t["accent"], t["ink"]) if primary else (t["card"], t["line"], t["text"])
    body = (f'<text x="{w / 2 - 8}" y="27" text-anchor="middle" font-size="14" font-weight="600" style="fill:{ink}">{text}</text>'
            f'<path d="M{w - 34} 25 l7 -7 m-5 0 h5 v5" stroke="{ink}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')
    return svg({**t, "card": fill, "line": stroke}, 42, body, w=round(w), rx=21)


def fetch_leetcode():
    query = ("query($u:String!){matchedUser(username:$u){submitStatsGlobal{acSubmissionNum{difficulty count}}"
             "profile{ranking}} allQuestionsCount{difficulty count}}")
    req = urllib.request.Request(
        "https://leetcode.com/graphql",
        data=json.dumps({"query": query, "variables": {"u": LEETCODE_USER}}).encode(),
        headers={"Content-Type": "application/json", "Referer": "https://leetcode.com", "User-Agent": "Mozilla/5.0"},
    )
    try:
        data = json.load(urllib.request.urlopen(req, timeout=20))["data"]
        solved = {r["difficulty"]: r["count"] for r in data["matchedUser"]["submitStatsGlobal"]["acSubmissionNum"]}
        totals = {r["difficulty"]: r["count"] for r in data["allQuestionsCount"]}
        return {k: (solved[k], totals[k]) for k in totals} | {"rank": data["matchedUser"]["profile"]["ranking"]}
    except Exception as e:  # noqa: BLE001 — any failure falls back to the last known numbers
        print(f"LeetCode fetch failed ({e}); using fallback numbers")
        return LEETCODE_FALLBACK


def main():
    lc = fetch_leetcode()
    for name, t in THEMES.items():
        cards = {
            "hero": hero(t), "metrics": metrics(t, lc["All"][0]), "leetcode": leetcode(t, lc),
            "stack": stack(t), "experience": experience(t), "extras": extras(t), "meme": meme(t),
        }
        cards |= {f"btn-{key}": button(t, text, primary) for key, text, primary in LINKS}
        for card, content in cards.items():
            (OUT / f"{card}-{name}.svg").write_text(content)
    print(f"Rendered {len(cards) * len(THEMES)} cards · LeetCode {lc['All'][0]} solved")


if __name__ == "__main__":
    main()
