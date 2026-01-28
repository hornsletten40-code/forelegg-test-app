import streamlit as st
import re
from itertools import product

# ============================================================
# KONFIGURASJON / JURIDISK GRUNNLAG
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

UNITS = {
    "beer_l": "liter",
    "wine_l": "liter",
    "spirits_l": "liter",
    "cigarettes": "stk",
    "tobacco_g": "gram"
}

LABELS = {
    "beer_l": "Øl",
    "wine_l": "Vin",
    "spirits_l": "Sprit",
    "cigarettes": "Sigaretter",
    "tobacco_g": "Tobakk / snus"
}

# ============================================================
# REGELMOTOR
# ============================================================

def excess(total, quota, persons):
    return max(0, total - quota * persons)

def fine_lookup(category, amount):
    if amount <= 0:
        return 0
    for limit, fine in FORELEGG_SATSER[category]:
        if amount <= limit:
            return fine
    return FORELEGG_SATSER[category][-1][1]

def optimal_distribution(category, excess_amount, persons):
    if excess_amount <= 0:
        return 0, [0] * persons

    best_total = float("inf")
    best_dist = None

    for dist in product(range(excess_amount + 1), repeat=persons):
        if sum(dist) != excess_amount:
            continue

        total = sum(fine_lookup(category, d) for d in dist)
        if total < best_total:
            best_total = total
            best_dist = list(dist)

    return best_total, best_dist

def calculate_optimal(data, persons):
    excesses = {k: excess(data[k], LEGAL_QUOTA[k], persons) for k in LEGAL_QUOTA}

    single_total = sum(fine_lookup(k, excesses[k]) for k in excesses)

    optimal_total = 0
    distributions = {}

    for k, ex in excesses.items():
        best, dist = optimal_distribution(k, ex, persons)
        optimal_total += best
        distributions[k] = dist

    return excesses, single_total, optimal_total, distributions

# ============================================================
# TEKSTTOLKING (CHAT → STRUKTUR)
# ============================================================

def parse_chat(text):
    text = text.lower()

    def find(pattern):
        m = re.search(pattern, text)
        return float(m.group(1)) if m else 0

    persons = int(find(r"(\d+)\s*(person|pers)")) or 1

    data = {
        "beer_l": find(r"(\d+(\.\d+)?)\s*liter\s*øl"),
        "wine_l": find(r"(\d+(\.\d+)?)\s*liter\s*vin"),
        "spirits_l": find(r"(\d+(\.\d+)?)\s*liter\s*(sprit|brennevin)"),
        "cigarettes": int(find(r"(\d+)\s*(sigaretter|sigg)")),
        "tobacco_g": find(r"(\d+)\s*(gram|g)\s*(snus|tobakk)")
    }

    return persons, data

# ============================================================
# STREAMLIT UI
# ============================================================

st.set_page_config(page_title="Forelegg – KI-agent", layout="centered")

st.title("🤖 KI-agent – Forenklet forelegg")
st.caption("Skriv hva de reisende har med seg. Agenten vurderer billigste lovlige forelegg.")

st.divider()

chat_input = st.chat_input(
    "Eksempel: 2 personer, 10 liter øl og 6 liter vin"
)

if chat_input:
    persons, data = parse_chat(chat_input)
    excesses, single_total, optimal_total, distributions = calculate_optimal(data, persons)

    with st.chat_message("assistant"):
        st.markdown("### 📊 Vurdering")

        st.markdown(f"**Antall reisende:** {persons}")

        st.markdown("**Overskytende mengde:**")
        for k, v in excesses.items():
            if v > 0:
                st.markdown(f"- {LABELS[k]}: {v} {UNITS[k]}")

        st.markdown("---")
        st.markdown(f"**Alternativ 1 – én person tar alt:** {single_total} kr")
        st.markdown(f"**Alternativ 2 – optimal fordeling:** {optimal_total} kr")

        if optimal_total < single_total:
            st.success("✅ Optimal fordeling av foreleggsvarer gir lavere samlet forelegg")

        if optimal_total > MAX_FORELEGG:
            st.error("❌ Overskrider maksgrense for forenklet forelegg")
            st.warning("➡️ Saken bør vurderes for ordinær straffesaksbehandling")

        st.markdown("---")
        st.markdown("### 👥 Optimal fordeling per person")

        for k, dist in distributions.items():
            if sum(dist) > 0:
                st.markdown(f"**{LABELS[k]}**")
                for i, amount in enumerate(dist, start=1):
                    if amount > 0:
                        st.markdown(f"- Person {i}: {amount} {UNITS[k]}")

        st.markdown("---")
        st.caption(
            "📚 Hjemmel: Vareførselsforskriften kapittel 12-11 • "
            "⚠️ Veiledende beregning – ikke vedtak"
        )
