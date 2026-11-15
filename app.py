from datetime import datetime
import streamlit as st
from ocr_engine import preprocess_and_extract
from allergen_matcher import load_allergen_db, scan_family_profiles

st.set_page_config(
    page_title="NutriScan | Hidden Allergen OCR Decoder",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern cards, hero banner, and ingredient pills
st.markdown(
    """
    <style>
    .hero-box {
        background: linear-gradient(135deg, #0F766E 0%, #0D9488 55%, #14B8A6 100%);
        padding: 1.6rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 1.2rem;
        box-shadow: 0 10px 25px -5px rgba(13, 148, 136, 0.25);
    }
    .hero-box h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .hero-box p {
        margin: 0.4rem 0 0 0;
        opacity: 0.92;
        font-size: 1rem;
    }
    .matrix-card {
        padding: 1.1rem 1.2rem;
        border-radius: 14px;
        margin-bottom: 0.75rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    }
    .card-danger {
        background-color: #FEF2F2;
        border-left: 6px solid #DC2626;
        color: #7F1D1D;
    }
    .card-caution {
        background-color: #FFFBEB;
        border-left: 6px solid #D97706;
        color: #78350F;
    }
    .card-safe {
        background-color: #ECFDF5;
        border-left: 6px solid #059669;
        color: #064E3B;
    }
    .pill {
        display: inline-block;
        padding: 0.22rem 0.65rem;
        margin: 0.2rem;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .pill-safe {
        background-color: #E2E8F0;
        color: #1E293B;
    }
    .pill-flagged {
        background-color: #FEE2E2;
        color: #B91C1C;
        border: 1px solid #FCA5A5;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

db = load_allergen_db()
all_categories = list(db.keys())

SAMPLE_LABELS = {
    "None (Upload or Capture Image)": "",
    "Sample 1: Creamy Pasta Sauce (Hidden Casein & Whey)": (
        "Ingredients: Crushed Tomatoes, Water, Olive Oil, Sodium Caseinate, Whey Protein Concentrate, "
        "Garlic, Basil, Sea Salt, Spices. May contain traces of soy and tree nuts."
    ),
    "Sample 2: Chocolate Energy Bar (Hidden Arachis & Soy Lecithin)": (
        "Ingredients: Rolled Oats, Cane Sugar, Arachis Hypogaea Paste, Cocoa Butter, Soy Lecithin, "
        "Barley Malt Extract, Natural Vanilla Flavor, Salt."
    ),
    "Sample 3: Organic Quinoa Crackers (Allergen-Free)": (
        "Ingredients: Organic Quinoa Flour, Brown Rice Flour, Sunflower Oil, Chia Seeds, "
        "Rosemary Extract, Sea Salt."
    ),
}

# Initialize Session State
if "family" not in st.session_state:
    st.session_state.family = {
        "Mom": ["Gluten / Wheat"],
        "Leo": ["Peanuts", "Milk / Dairy"],
        "Dad": ["Soy"],
    }
if "history" not in st.session_state:
    st.session_state.history = []

# Sidebar: Family Profile Manager & Engine Settings
with st.sidebar:
    st.header("👨‍👩‍👧‍👦 Family Profiles")
    st.caption("Configure household dietary restrictions for simultaneous scanning.")

    col_add1, col_add2 = st.columns([2.2, 1])
    with col_add1:
        new_member = st.text_input("New member", placeholder="e.g., Maya", label_visibility="collapsed")
    with col_add2:
        if st.button("Add", use_container_width=True) and new_member.strip():
            name = new_member.strip()
            if name not in st.session_state.family:
                st.session_state.family[name] = []
                st.rerun()

    for member in list(st.session_state.family.keys()):
        with st.expander(f"**{member}** ({len(st.session_state.family[member])} active)", expanded=True):
            st.session_state.family[member] = st.multiselect(
                f"Allergies for {member}",
                options=all_categories,
                default=st.session_state.family[member],
                key=f"select_{member}",
                label_visibility="collapsed",
            )
            if len(st.session_state.family) > 1:
                if st.button(f"Remove {member}", key=f"del_{member}"):
                    del st.session_state.family[member]
                    st.rerun()

    st.divider()
    st.header("⚙️ OCR & Matching Engine")
    prep_mode = st.selectbox(
        "OpenCV Preprocessing Pipeline",
        [
            "NutriScan Adaptive Pipeline",
            "Sauvola Local Binarization",
            "Global Otsu Thresholding",
            "Raw Image",
        ],
    )
    fuzzy_cutoff = st.slider(
        "Fuzzy Typo Tolerance (%)",
        min_value=75,
        max_value=100,
        value=86,
        help="Lower values catch heavier OCR character misreads (e.g., 'caseln' -> 'casein').",
    )

# Hero Banner
st.markdown(
    """
    <div class="hero-box">
        <h1>🔬 NutriScan: Hidden Allergen OCR Decoder</h1>
        <p>Instant food-label optical character recognition, scientific synonym decoding, multi-user family safety matrix & smart shelf substitutions.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_scan, tab_wiki, tab_hist = st.tabs(["📸 Label Scanner", "📚 Hidden Allergen Encyclopedia", "🕒 Scan History"])

with tab_scan:
    input_method = st.radio(
        "Choose Input Source",
        ["📁 Upload Label Photo", "📷 Live Webcam Capture", "🧪 Quick Demo Sample"],
        horizontal=True,
    )

    image_source = None
    preset_text = ""
    avg_conf = None

    if input_method == "📁 Upload Label Photo":
        image_source = st.file_uploader("Upload food ingredient packaging photo", type=["jpg", "jpeg", "png", "webp"])
    elif input_method == "📷 Live Webcam Capture":
        image_source = st.camera_input("Align the ingredient list inside the frame and capture")
    else:
        sample_choice = st.selectbox("Select a test ingredient label", list(SAMPLE_LABELS.keys()))
        preset_text = SAMPLE_LABELS[sample_choice]

    if image_source is not None:
        with st.spinner("Running OpenCV image enhancement & Tesseract OCR..."):
            extracted_text, processed_img, avg_conf = preprocess_and_extract(image_source, mode=prep_mode)

        m1, m2, m3 = st.columns(3)
        m1.metric("Active Family Profiles", len(st.session_state.family))
        m2.metric("OCR Confidence Score", f"{avg_conf}%")
        m3.metric("Pipeline Mode", prep_mode.split()[0])

        c1, c2 = st.columns(2)
        with c1:
            st.image(image_source, caption="Original Food Packaging", use_container_width=True)
        with c2:
            st.image(processed_img, caption=f"Enhanced Binary Input ({prep_mode})", use_container_width=True)

        active_text = extracted_text
    else:
        active_text = preset_text

    st.subheader("📝 Decoded Ingredient Text")
    edited_text = st.text_area(
        "Review or edit extracted text before running the family check:",
        value=active_text,
        height=115,
        placeholder="Upload a label image or choose a Quick Demo Sample above...",
    )

    if st.button("🔍 Scan All Family Profiles", type="primary", use_container_width=True, disabled=not edited_text.strip()):
        scan_output = scan_family_profiles(edited_text, st.session_state.family, db, fuzzy_threshold=fuzzy_cutoff)
        member_results = scan_output["members"]
        tokens = scan_output["tokens"]

        # Save to history
        st.session_state.history.insert(
            0,
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "snippet": edited_text[:70] + ("..." if len(edited_text) > 70 else ""),
                "summary": {m: r["status"] for m, r in member_results.items()},
            },
        )

        # Highlighted Token Pills
        all_flagged_terms = set()
        for r in member_results.values():
            for df in r["direct_flags"]:
                for h in df["hits"]:
                    all_flagged_terms.add(h["matched_text"].lower())

        st.subheader("🏷️ Tokenized Ingredient Breakdown")
        pills_html = ""
        for tok in tokens:
            is_bad = any(term in tok or tok in term for term in all_flagged_terms)
            css_cls = "pill-flagged" if is_bad else "pill-safe"
            prefix = "⚠️ " if is_bad else ""
            pills_html += f'<span class="pill {css_cls}">{prefix}{tok}</span>'
        st.markdown(pills_html, unsafe_allow_html=True)

        # Family Safety Matrix Cards
        st.subheader("🛡️ Family Safety Matrix")
        cols = st.columns(len(member_results))
        for idx, (member, res) in enumerate(member_results.items()):
            with cols[idx]:
                if res["status"] == "DANGER":
                    st.markdown(
                        f'<div class="matrix-card card-danger"><strong>🚨 DANGER for {member}</strong><br>'
                        f'<small>{len(res["direct_flags"])} allergen trigger(s) found</small></div>',
                        unsafe_allow_html=True,
                    )
                elif res["status"] == "CAUTION":
                    st.markdown(
                        f'<div class="matrix-card card-caution"><strong>⚠️ CAUTION for {member}</strong><br>'
                        f'<small>Precautionary trace warning</small></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="matrix-card card-safe"><strong>✅ SAFE for {member}</strong><br>'
                        f'<small>No listed allergens detected</small></div>',
                        unsafe_allow_html=True,
                    )

        # Detailed Warnings & Smart Substitutions
        report_lines = [f"NutriScan Safety Report ({datetime.now().strftime('%Y-%m-%d %H:%M')})", "=" * 50, ""]
        for member, res in member_results.items():
            report_lines.append(f"{member}: {res['status']}")
            if res["direct_flags"] or res["trace_flags"]:
                st.markdown(f"#### Detailed Breakdown for **{member}**")
                for flag in res["direct_flags"]:
                    hit_labels = [
                        f"`{h['matched_text']}` → **{h['term']}** ({h['type']} {h['score']}%)"
                        for h in flag["hits"]
                    ]
                    st.error(
                        f"{flag['icon']} **{flag['category']}** detected: {', '.join(hit_labels)}\n\n"
                        f"**Why it matters:** {flag['explanation']}\n\n"
                        f"**🛒 Safe Shelf Alternatives:** {' • '.join(flag['alternatives'])}"
                    )
                    report_lines.append(f"  - DANGER ({flag['category']}): {', '.join(h['term'] for h in flag['hits'])}")
                    report_lines.append(f"    Alternatives: {', '.join(flag['alternatives'])}")

                for tflag in res["trace_flags"]:
                    terms = ", ".join(h["term"] for h in tflag["hits"])
                    st.warning(
                        f"{tflag['icon']} **Cross-Contamination Notice ({tflag['category']}):** "
                        f"Label includes precautionary warning for `{terms}`."
                    )
                    report_lines.append(f"  - CAUTION (Trace {tflag['category']}): {terms}")

        st.download_button(
            "📄 Download Family Safety Report (.txt)",
            data="\n".join(report_lines),
            file_name="nutriscan_safety_report.txt",
            mime="text/plain",
        )

        st.info(
            "**Medical & Safety Disclaimer:** NutriScan is an assistive informational tool. "
            "Accuracy depends on photo clarity and OCR performance. Always verify physical packaging directly."
        )

with tab_wiki:
    st.subheader("📚 Hidden Scientific & Chemical Allergen Dictionary")
    st.write("Explore the hidden ingredient synonyms and safe shelf alternatives stored in NutriScan's reference database.")
    for cat, info in db.items():
        with st.expander(f"{info.get('icon', '🔹')} **{cat}** ({len(info['keywords'])} tracked terms)"):
            st.write(f"**Description:** {info['explanation']}")
            st.write("**Tracked Keywords & Scientific Synonyms:** `" + "`, `".join(info["keywords"]) + "`")
            st.write("**Recommended Safe Substitutes:** " + " | ".join(info["alternatives"]))

with tab_hist:
    st.subheader("🕒 Recent Scans (Current Session)")
    if not st.session_state.history:
        st.caption("No scans run yet in this session.")
    else:
        for item in st.session_state.history:
            badges = "  |  ".join([f"**{m}:** {s}" for m, s in item["summary"].items()])
            st.markdown(f"- `{item['time']}` — {badges}  \n  *Label:* `{item['snippet']}`")
