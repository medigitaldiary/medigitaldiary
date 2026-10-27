import os
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path("info-card.svg")
STATIC = os.environ.get("STATIC") == "1"   # STATIC=1 gives a frozen frame for previews

THEME = "light"            # match the portrait: "light" or "dark"
W = 490                    # card width (the README shows it at this width)
PAD = 22
LH = 17                    # line height
FS = 11                    # font size
KEYW = 98                  # width of the left (label) column
BAR = 32                   # title bar height
STAGGER = 0.11             # seconds between lines
START = 0.3

PALETTES = {
    "light": dict(bg="#f6f8fa", bar="#eaeef2", line="#d0d7de", text="#24292f",
                  key="#0969da", muted="#6e7781", accent="#1a7f37"),
    "dark": dict(bg="#0d1117", bar="#161b22", line="#30363d", text="#c9d1d9",
                 key="#58a6ff", muted="#8b949e", accent="#3fb950"),
}
C = PALETTES[THEME]

# ---- CONTENT: edit freely. kinds: title, rule, kv, section, blank ----
ROWS = [
    ("title", "megh@github"),
    ("rule",),
    ("kv", "Now", "Founding PM at BondScanner, a SEBI-regulated"),
    ("kv", "", "bond platform (Tap Invest)"),
    ("kv", "Prev", "Product intern at MoveInSync"),
    ("kv", "Edu", "BITS Pilani Goa, B.E. Chem + M.Sc. Bio Sci '25"),
    ("kv", "Stack", "Claude API, Python, TypeScript, SQL, Figma, MoEngage"),
    ("blank",),
    ("section", "Highlights"),
    ("kv", "Referral", "Redesigned the referral flow in onboarding:"),
    ("kv", "", "40% referral adoption, +20% acquisition (3 mo)"),
    ("kv", "AI call", "Sarvam STT + Claude score RM calls and write"),
    ("kv", "analysis", "action items; team quality up ~15% in 30 days"),
    ("kv", "Data", "Deridata bond API: 5 endpoints analysed across"),
    ("kv", "partnership", "94 live ISINs, specced into deal-page sections"),
    ("kv", "Support pod", "Freshdesk SLAs and ticket automations cut"),
    ("kv", "", "manual support effort by 40%"),
    ("blank",),
    ("kv", "Site", "meghgupta.in"),
    ("kv", "Resume", "Google Drive (PDF)"),
    ("kv", "LinkedIn", "linkedin.com/in/meghxgupta"),
]
# -----------------------------------------------------------------------

FONT = "ui-monospace, SFMono-Regular, Consolas, Menlo, monospace"


def row_group(i, inner):
    t = START + i * STAGGER
    if STATIC:
        return f"<g>{inner}</g>"
    return (
        f'<g opacity="0">'
        f'<animate attributeName="opacity" from="0" to="1" dur="0.35s" begin="{t:.2f}s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" from="0 6" to="0 0" dur="0.35s" begin="{t:.2f}s" fill="freeze"/>'
        f"{inner}</g>"
    )


def build():
    H = BAR + 16 + len(ROWS) * LH + 14
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" fill="{C["bg"]}" stroke="{C["line"]}"/>',
        f'<path d="M0.5 10 a9.5 9.5 0 0 1 9.5 -9.5 H{W-10} a9.5 9.5 0 0 1 9.5 9.5 V{BAR} H0.5 Z" fill="{C["bar"]}"/>',
        f'<line x1="0.5" y1="{BAR}" x2="{W-0.5}" y2="{BAR}" stroke="{C["line"]}"/>',
        f'<circle cx="18" cy="{BAR/2}" r="5" fill="#ff5f56"/>',
        f'<circle cx="36" cy="{BAR/2}" r="5" fill="#ffbd2e"/>',
        f'<circle cx="54" cy="{BAR/2}" r="5" fill="#27c93f"/>',
        f'<text x="{W/2}" y="{BAR/2+4}" text-anchor="middle" font-family="{FONT}" font-size="10.5" fill="{C["muted"]}">megh@github: ~</text>',
        f'<g font-family="{FONT}" font-size="{FS}">',
    ]
    y0 = BAR + 16 + FS
    for i, row in enumerate(ROWS):
        y = y0 + i * LH
        kind = row[0]
        inner = ""
        if kind == "title":
            inner = f'<text x="{PAD}" y="{y}" font-weight="700" fill="{C["accent"]}">{escape(row[1])}</text>'
        elif kind == "rule":
            inner = f'<text x="{PAD}" y="{y}" fill="{C["muted"]}">{"-" * 45}</text>'
        elif kind == "section":
            inner = f'<text x="{PAD}" y="{y}" font-weight="700" fill="{C["accent"]}">{escape(row[1])}</text>'
        elif kind == "kv":
            key = f'<text x="{PAD}" y="{y}" font-weight="600" fill="{C["key"]}">{escape(row[1])}</text>' if row[1] else ""
            val = f'<text x="{PAD + KEYW}" y="{y}" fill="{C["text"]}">{escape(row[2])}</text>'
            inner = key + val
        else:
            continue
        p.append(row_group(i, inner))
    p.append("</g></svg>")
    return "\n".join(p)


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"Saved {OUT}" + (" (static)" if STATIC else ""))
