import streamlit as st

# ============================================================
# KONFIGURASJON
# ============================================================

MAX_FORELEGG = 20000  # maksgrense for forenklet forelegg (kr)

LEGAL_QUOTA = {
    "beer_l": 16,
    "wine_l": 4,
    "spirits_l": 1,
    "cigarettes": 200,
    "tobacco_g": 250
}

FORELEGG_SATSER = {
    "beer_l": [(10, 400),(20, 800),(30, 1600),(40, 2500),(50, 3400),(60, 4500),(80, 7000),(100, 9500)],
    "wine_l": [(2, 400),(4, 800),(6, 1600),(8, 2500),(10, 3400),(12, 4500),(16, 7000),(20, 9500)],
    "spirits_l": [(1, 400),(2, 800),(3, 1600),(4, 2500),(5, 3400),(6, 4500),(8, 7000),(10, 9500)],
    "cigarettes": [(400, 400),(600, 800),(800, 1600),(1000, 2500),(1200, 3600),(1600, 6100),(2000, 8600)],
    "tobacco_g": [(500, 400),(750, 800),(1000, 1600),(1250, 2500),(1500, 3600),(2000, 6100)]
}

UNITS = {
    "beer_l": "liter",
    "wine_l": "liter",
    "spirits_l": "liter",
    "cigarettes": "stk",
    "tobacco_g": "gram"
}


# ============================================================
# REGELMOTOR
# ============================================================

def excess(total, quota, persons):
    return max(0, total - quota * persons)

def fine_lookup(cat, ex):
    if ex <= 0:
        return 0
    for limit, fine in FORELEGG_SATSER[cat]:
        if ex <= limit:
            return fine
    return FORELEGG_SATSER[cat][-1][1]

def calculate(data, persons):
    excesses = {k: excess(data[k], LEGAL_QUOTA[k], persons) for k in LEGAL_QUOTA}
    fines = {k: fine_lookup(k, excesses[k]) for k in excesses}
    total = sum(fines.values())
    return excesses, fines, total


# ============================================================
# UI
# ============================================================

st.set_page_config(page_title="Foreleggskalkulator", layout="centered")

st.title("🚨 Forenklet forelegg – testapp")
st.caption("Vareførselsforskriften kap. 12-11 • Beslutningsstøtte")

st.divider()

persons = st.number_input("Antall personer", min_value=1, step=1, value=1)

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
    st.divider()

    # Beregn for 1 person
    _, _, total_single = calculate(data, 1)

    # Beregn delt
    excesses, fines, total_split = calculate(data, persons)

    st.subheader("📊 Resultat")

    for k, v in excesses.items():
        st.write(f"**{k}**: {v} {UNITS[k]}")

    st.divider()

    st.write(f"**Forelegg (1 person):** {total_single} kr")
    st.write(f"**Forelegg delt på {persons} personer:** {total_split} kr")
    st.write(f"**Per person:** {round(total_split/persons,2)} kr")

    # 🔍 Forslag om deling
    if persons > 1 and total_split < total_single:
        st.success("✅ Deling gir lavere samlet forelegg")

    # 🚨 Maksgrense
    if total_split > MAX_FORELEGG:
        st.error("❌ Beløpet overstiger maksgrense for forenklet forelegg")
        st.warning("➡️ Saken må vurderes for ordinær straffesaksbehandling")

    st.caption("⚠️ Veiledende beregning – endelig avgjørelse tas av saksbehandler")
