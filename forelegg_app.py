import streamlit as st
import re
from itertools import product

# ============================================================
# REGELBASE – KVOTER MED HJEMMEL
# ============================================================

QUOTA_RULES = {
    "beer_l": {
        "name": "Øl (≤ 4,7 %)",
        "quota_per_person": 16,
        "unit": "liter",
        "home": "Vareførselsforskriften § 12-11-2 første ledd bokstav a"
    },
    "wine_l": {
        "name": "Vin (4,7–22 %)",
        "quota_per_person": 4,
        "unit": "liter",
        "home": "Vareførselsforskriften § 12-11-2 første ledd bokstav b"
    },
    "spirits_l": {
        "name": "Brennevin (22–60 %)",
        "quota_per_person": 1,
        "unit": "liter",
        "home": "Vareførselsforskriften § 12-11-2 første ledd bokstav c"
    },
    "cigarettes": {
        "name": "Sigaretter",
        "quota_per_person": 200,
        "unit": "stk",
        "home": "Vareførselsforskriften § 12-11-1"
    },
    "tobacco_g": {
        "name": "Tobakk / snus",
        "quota_per_person": 250,
        "unit": "gram",
        "home": "Vareførselsforskriften § 12-11-1"
    }
}

FORELEGG_SATSER = {
    "beer_l": [(10,400),(20,800),(30,1600),(40,2500)],
    "wine_l": [(2,400),(4,800),(6,1600),(8,2500)],
    "spirits_l": [(1,400),(2,800),(3,1600),(4,2500)],
    "cigarettes": [(400,400),(600,800),(800,1600),(1000,2500)],
    "tobacco_g": [(500,400),(750,800),(1000,1600),(1250,2500)]
}

MAX_FORELEGG = 20000

# ============================================================
# REGELMOTOR
# ============================================================

def fine_lookup(category, amount):
    if amount <= 0:
        return 0
    for limit, fine in FORELEGG_SATSER[category]:
        if amount <= limit:
            return fine
    return FORELEGG_SATSER[category][-1][1]

def get_quota(category, persons):
    rule = QUOTA_RULES[category]
    return rule["quota_per_person"] * persons, rule["home"]

def excess(total, category, persons):
    quota, _ = get_quota(category, persons)
    return max(0, total - quota)

def optimal_distribution(category, excess_amount, persons):
    if excess_amount <= 0:
        return 0, [0] * persons

    step = 0.5 if category.endswith("_l") else 1
    steps = int(round(excess_amount / step))

    best_total = float("inf")
    best_dist = None

    for dist_steps in product(range(steps + 1), repeat=persons):
        if sum(dist_steps) != steps:
            continue

        dist_amounts = [d * step for d in dist_steps]
        total = sum(fine_lookup(category, amt) for amt in dist_amounts)

        if total < best_total:
            best_total = total
            best_dist = dist_amounts

    return best_total, best_dist

def calculate(data, persons):
    results = {}
    single_total = 0
    optimal_total = 0

    for k, total_amount in data.items():
        ex = excess(total_amount, k, persons)
        quota, home = get_quota(k, persons)

        single_fine = fine_lookup(k, ex)
        best_fine, best_dist = optimal_distribution(k, ex, persons)

        single_total += single_fine
        optimal_total += best_fine

        results[k] = {
            "total": total_amount,
            "quota": quota,
            "excess": ex,
            "home": home,
            "distribution": best_dist
        }

    return results, single_total, optimal_total

# ============================================================
# TEKSTTOLKING (ROBUST)
# ============================================================

def parse_text(text):
    t = text.lower().replace(",", ".")

    def num(p):
        m = re.search(p, t)
        return float(m.group(1)) if m else 0

    persons = int(num(r"(\d+)\s*(person|pers)")) or 1

    return persons, {
        "beer_l": num(r"(\d+(\.\d+)?)\s*(l|liter).*øl"),
        "wine_l": num(r"(\d+(\.\d+)?)\s*(l|liter).*vin"),
        "spirits_l": num(r"(\d+(\.\d+)?)\s*(l|liter).*(sprit|brennevin)"),
        "cigarettes": int(num(r"(\d+)\s*(sigaretter|sigg)")),
        "tobacco_g": num(r"(\d+(\.\d+)?)\s*(g|gram).*(snus|tobakk)")
    }

# ============================================================
# STREAMLIT UI
# ============================================================

st.set_page_config(page_title="KI-agent – forelegg", layout="centered")

st.title("⚖️ KI-agent – forenklet forelegg")
st.caption("Kvoter og beregning hentet fra regelbase med hjemmel")

query = st.chat_input("Eksempel: 2 personer, 40 liter øl")

if query:
    persons, data = parse_text(query)

    with st.chat_message("assistant"):
        if sum(data.values()) == 0:
            st.warning("Jeg klarte ikke å tolke mengder fra teksten.")
        else:
            results, single, optimal = calculate(data, persons)

            st.markdown(f"### 📊 Vurdering ({persons} reisende)")

            for k, r in results.items():
                if r["excess"] > 0:
                    st.markdown(
                        f"- **{QUOTA_RULES[k]['name']}**: "
                        f"{r['excess']} {QUOTA_RULES[k]['unit']} overskytende  \n"
                        f"  *Lovlig kvote:* {r['quota']} {QUOTA_RULES[k]['unit']}  \n"
                        f"  *Hjemmel:* {r['home']}"
                    )

            st.markdown(f"**Én person tar alt:** {single} kr")
            st.markdown(f"**Optimal fordeling:** {optimal} kr")

            if optimal < single:
                st.success("Optimal fordeling av foreleggsvarer gir lavere samlet forelegg")

            if optimal > MAX_FORELEGG:
                st.error("Overskrider maksgrense for forenklet forelegg")

            st.caption("⚠️ Beslutningsstøtte – ikke vedtak")
