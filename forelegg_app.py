import streamlit as st
from itertools import product

# ============================================================
# KONFIGURASJON / JURIDISK GRUNNLAG
# ============================================================

MAX_FORELEGG = 20000  # maksgrense for forenklet forelegg

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
    """
    Finner laveste samlede forelegg ved å fordele overskytende mengde
    på flere personer (uten å dele beløp).
    """
    if excess_amount <= 0:
        return 0, [0] * persons

    best_total = float("inf")
    best_dist = None

    # Bruteforce – trygt for realistisk bruk (1–3 personer)
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

    # Alternativ 1 – én person tar alt
    single_total = sum(fine_lookup(k, excesses[k]) for k in excesses)

    # Alternativ 2 – optimal fordeling
    optimal_total = 0
    distributions = {}

    for k, ex in excesses.items():
        best, dist = optimal_distribution(k, ex, persons)
        optimal_total += best
        distributions[k] = dist

    return excesses, single_total, optimal_total, distributions


# ============================================================
# STREAMLIT UI
# ============================================================

st.set_page_config(page_title="Forelegg – KI-agent", layout="centered")

st.title("🚨 Forenklet forelegg – KI-agent")
st.caption("Vareførselsforskriften kapittel 12-11 • Beslutningsstøtte")

st.divider()

persons = st.number_input("Antall reisende", min_value=1, step=1, value=1)

beer = st.number_input("Øl (liter)", min_value=0.0, step=0.5)
wine = st.number_input("Vin (liter)", min_value=0.0, step=0.5)
spirits = st.number_input("Sprit (liter)", min_value=0.0, step=0.5)
cigarettes = st.number_input("Sigaretter (stk)", min_value=0, step=50)
tobacco = st.number_input("Tobakk / snus (gram)", min_value=0.0, step=50.0)

data = {
    "beer_l": beer,
    "wine_l": wine,
    "spirits_l": spirits,
    "cigarettes": cigarettes,
    "tobacco_g": tobacco
}

if st.button("Beregn forelegg"):
    excesses, single_total, optimal_total, distributions = calculate_optimal(data, persons)

    st.divider()
    st.subheader("📊 Resultat")

    st.write("### Overskytende mengde")
    for k, v in excesses.items():
        if v > 0:
            st.write(f"• **{LABELS[k]}:** {v} {UNITS[k]}")

    st.divider()

    st.write(f"**Alternativ 1 – én person tar alt:** {single_total} kr")
    st.write(f"**Alternativ 2 – optimal fordeling:** {optimal_total} kr")

    if optimal_total < single_total:
        st.success("✅ Optimal fordeling av foreleggsvarer gir lavere samlet forelegg")

    if optimal_total > MAX_FORELEGG:
        st.error("❌ Overskrider maksgrense for forenklet forelegg")
        st.warning("➡️ Saken bør vurderes for ordinær straffesaksbehandling")

    st.divider()
    st.write("### Optimal fordeling per person")

    for k, dist in distributions.items():
        if sum(dist) > 0:
            st.write(f"**{LABELS[k]}**")
            for i, amount in enumerate(dist, start=1):
                if amount > 0:
                    st.write(f"– Person {i}: {amount} {UNITS[k]}")

    st.divider()
    st.caption(
        "📚 Hjemmel: Vareførselsforskriften kapittel 12-11 • "
        "⚠️ Veiledende beregning – ikke vedtak"
    )
