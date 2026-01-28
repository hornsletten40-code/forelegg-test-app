import streamlit as st
import re
from itertools import product

# ============================================================
# KONFIG
# ============================================================

MAX_FORELEGG = 20000

LEGAL_QUOTA = {
    "beer_l": 16,
    "wine_l": 4,
    "spirits_l": 1,
    "cigarettes": 200,
    "tobacco_g": 250
}

FORELEGG_SATSER = {
    "beer_l": [(10,400),(20,800),(30,1600),(40,2500),(50,3400),(60,4500),(80,7000),(100,9500)],
    "wine_l": [(2,400),(4,800),(6,1600),(8,2500),(10,3400),(12,4500),(16,7000),(20,9500)],
    "spirits_l": [(1,400),(2,800),(3,1600),(4,2500),(5,3400),(6,4500),(8,7000),(10,9500)],
    "cigarettes": [(400,400),(600,800),(800,1600),(1000,2500),(1200,3600),(1600,6100),(2000,8600)],
    "tobacco_g": [(500,400),(750,800),(1000,1600),(1250,2500),(1500,3600),(2000,6100)]
}

LABELS = {
    "beer_l": "Øl",
    "wine_l": "Vin",
    "spirits_l": "Sprit",
    "cigarettes": "Sigaretter",
    "tobacco_g": "Tobakk / snus"
}

UNITS = {
    "beer_l": "liter",
    "wine_l": "liter",
    "spirits_l": "liter",
    "cigarettes": "stk",
    "tobacco_g": "gram"
}

# ============================================================
# RESTRIKSJONSBELAGTE VARER (v1)
# ============================================================

RESTRICTED_ITEMS = {
    "pepperspray": {
        "status": "forbudt",
        "reaction": "Beslag og straffesak",
        "law": "Våpenforskriften § 3"
    },
    "fyrverkeri": {
        "status": "tillatelse",
        "reaction": "Beslag / anmeldelse ved manglende tillatelse",
        "law": "Forskrift om håndtering av eksplosjonsfarlig stoff"
    },
    "kniv": {
        "status": "avhengig",
        "reaction": "Kan beslaglegges",
        "law": "Våpenloven § 5"
    },
    "narkotika": {
        "status": "forbudt",
        "reaction": "Straffesak",
        "law": "Legemiddelloven / straffeloven"
    },
    "legemidler": {
        "status": "tillatelse",
        "reaction": "Dokumentasjonskrav",
        "law": "Legemiddelloven"
    }
}

# ============================================================
# REGELMOTOR
# ============================================================

def excess(total, quota, persons):
    return max(0, total - quota * persons)

def fine_lookup(cat, amount):
    if amount <= 0:
        return 0
    for limit, fine in FORELEGG_SATSER[cat]:
        if amount <= limit:
            return fine
    return FORELEGG_SATSER[cat][-1][1]

def optimal_distribution(cat, excess_amount, persons):
    if excess_amount <= 0:
        return 0, [0]*persons

    best_total = float("inf")
    best_dist = None

    for dist in product(range(excess_amount + 1), repeat=persons):
        if sum(dist) != excess_amount:
            continue
        total = sum(fine_lookup(cat, d) for d in dist)
        if total < best_total:
            best_total = total
            best_dist = list(dist)

    return best_total, best_dist

def calculate(data, persons):
    excesses = {k: excess(data[k], LEGAL_QUOTA[k], persons) for k in LEGAL_QUOTA}
    single = sum(fine_lookup(k, excesses[k]) for k in excesses)

    optimal = 0
    dist = {}
    for k, ex in excesses.items():
        best, d = optimal_distribution(k, ex, persons)
        optimal += best
        dist[k] = d

    return excesses, single, optimal, dist

# ============================================================
# FORBEDRET TEKSTTOLKING
# ============================================================

def normalize(text):
    return text.lower().replace(",", ".")

def parse_text(text):
    t = normalize(text)

    def num(p):
        m = re.search(p, t)
        return float(m.group(1)) if m else 0

    persons = int(num(r"(\d+)\s*(person|pers)")) or 1

    beer = num(r"(\d+)\s*kasse\s*øl") * 12 + num(r"(\d+(\.\d+)?)\s*liter\s*øl")
    beer += num(r"(\d+)\s*(boks|flaske)\s*øl") * 0.5

    wine = num(r"(\d+)\s*flaske\s*vin") * 0.75 + num(r"(\d+(\.\d+)?)\s*liter\s*vin")

    spirits = num(r"(\d+(\.\d+)?)\s*liter\s*(sprit|brennevin)")
    if "halv liter" in t or "½ liter" in t:
        spirits += 0.5

    cigarettes = int(num(r"(\d+)\s*kartong")) * 200 + int(num(r"(\d+)\s*pakke")) * 20

    tobacco = num(r"(\d+)\s*(g|gram)\s*(snus|tobakk)")

    return persons, {
        "beer_l": beer,
        "wine_l": wine,
        "spirits_l": spirits,
        "cigarettes": cigarettes,
        "tobacco_g": tobacco
    }

def check_restricted(text):
    for item, info in RESTRICTED_ITEMS.items():
        if item in text.lower():
            return item, info
    return None, None

# ============================================================
# STREAMLIT UI
# ============================================================

st.title("🤖 KI-agent – Toll / forelegg")
st.caption("Skriv hva de reisende har med seg – eller spør om en vare")

query = st.chat_input(
    "Eksempel: 2 personer, 1 kasse øl og 6 flasker vin"
)

if query:
    item, info = check_restricted(query)

    with st.chat_message("assistant"):
        if item:
            st.markdown(f"### ⚠️ Restriksjonsbelagt vare: **{item}**")
            st.markdown(f"- **Status:** {info['status']}")
            st.markdown(f"- **Reaksjon:** {info['reaction']}")
            st.markdown(f"- **Hjemmel:** {info['law']}")
            st.caption("⚠️ Veiledende informasjon – ikke vedtak")
        else:
            persons, data = parse_text(query)
            st.write("DEBUG – tolket data:", persons, data)

            excesses, single, optimal, dist = calculate(data, persons)

            st.markdown(f"### 📊 Vurdering ({persons} reisende)")
            for k, v in excesses.items():
                if v > 0:
                    st.markdown(f"- {LABELS[k]}: {v} {UNITS[k]}")

            st.markdown(f"**Én person tar alt:** {single} kr")
            st.markdown(f"**Optimal fordeling:** {optimal} kr")

            if optimal < single:
                st.success("Optimal fordeling gir lavere samlet forelegg")

            if optimal > MAX_FORELEGG:
                st.error("Overskrider maksgrense for forenklet forelegg")

            st.markdown("#### 👥 Optimal fordeling")
            for k, d in dist.items():
                if sum(d) > 0:
                    st.markdown(f"**{LABELS[k]}**")
                    for i, a in enumerate(d, 1):
                        if a > 0:
                            st.markdown(f"- Person {i}: {a} {UNITS[k]}")

            st.caption("📚 Vareførselsforskriften kap. 12-11 • Veiledende")

