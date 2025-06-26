import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from io import BytesIO
import io

# === CONFIGURATION DE LA PAGE ===
st.set_page_config(page_title="Analyse des Taux Zéro-Coupon", layout="wide")

# === STYLES PERSONNALISÉS ===
def set_theme(theme):
    if theme == "Sombre":
        st.markdown("""
            <style>
                html, body, .stApp {
                    background-color: #000000;
                    color: #f8f8f8;
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 16px;
                }
                h1, h2, h3, h4 {
                    color: #00ffe1;
                }
                .stButton>button, .stDownloadButton>button {
                    background-color: #00ffe1;
                    color: #000000;
                    border-radius: 5px;
                    padding: 0.5em 1em;
                    font-weight: bold;
                }
                .stTextInput>div>div>input,
                .stFileUploader>div>div {
                    background-color: #111111;
                    color: #f8f8f8;
                }
                .stCheckbox>label, .stSelectbox label {
                    color: #f8f8f8;
                }
                .stExpanderHeader {
                    background-color: #111111 !important;
                    color: #f8f8f8 !important;
                }
                .element-container:has(.dataframe) {
                    max-height: 400px;
                    overflow: auto;
                }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
                html, body, .stApp {
                    background-color: #ffffff;
                    color: #0e1117;
                    font-family: 'Segoe UI', sans-serif;
                    font-size: 16px;
                }
                h1, h2, h3, h4 {
                    color: #007bff;
                }
                .stButton>button, .stDownloadButton>button {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 5px;
                    padding: 0.5em 1em;
                    font-weight: bold;
                }
                .stTextInput>div>div>input,
                .stFileUploader>div>div {
                    background-color: #ffffff;
                    color: #0e1117;
                }
                .stCheckbox>label, .stSelectbox label {
                    color: #0e1117;
                }
                .stExpanderHeader {
                    background-color: #f2f2f2 !important;
                    color: #0e1117 !important;
                }
                .element-container:has(.dataframe) {
                    max-height: 400px;
                    overflow: auto;
                }
            </style>
        """, unsafe_allow_html=True)

# === SIDEBAR ===
st.sidebar.header("🎛 Options")
theme = st.sidebar.selectbox("🎨 Thème", ["Clair", "Sombre"])
set_theme(theme)
affichage_tableaux = st.sidebar.checkbox("Afficher les tableaux", value=True)

# === TITRE ===
st.title("Analyse de la Martingalité")
st.markdown("Téléversez un fichier `.csv` (point-virgule, ISO-8859-1) pour analyser les déflateurs et l'écart à la martingalité.")

# === UPLOAD ===
uploaded_file = st.file_uploader("📂 Téléversez votre fichier CSV", type=["csv"])

if uploaded_file:
    try:
        df_zc = pd.read_csv(uploaded_file, sep=";", encoding="ISO-8859-1")

        def analyse_taux_zc(df_zc):
            def extraire_zc_1_year(df_zc):
                df_1y = df_zc[df_zc["Maturité"] == 1].copy()
                df_1y = df_1y.drop(columns=["Maturité"])
                df_1y = df_1y.set_index("TRAJECTOIRE").sort_index()
                return df_1y

            def calcul_deflateurs_simulés(zc_1y):
                zc_1y.columns = zc_1y.columns.astype(int)
                deflateurs = pd.DataFrame(index=zc_1y.index, columns=zc_1y.columns)
                for traj in zc_1y.index:
                    for t in zc_1y.columns:
                        taux = zc_1y.loc[traj, t]
                        if t == 0:
                            deflateurs.loc[traj, t] = 1 / (1 + taux)
                        else:
                            deflateurs.loc[traj, t] = deflateurs.loc[traj, t - 1] * (1 / (1 + taux))
                deflateurs = deflateurs.mean().astype(float)
                deflateurs.index = deflateurs.index + 1
                deflateurs = deflateurs.iloc[:-1]
                return deflateurs

            def extraire_courbe_centrale(df_zc):
                df_filtré = df_zc[(df_zc["TRAJECTOIRE"] == 1) & (df_zc["Maturité"].between(1, 50))].copy()
                courbe = df_filtré[["Maturité", "0"]].set_index("Maturité").sort_index()
                courbe.columns = ["Taux courbe centrale"]
                return courbe

            def calculer_deflateur_central(courbe):
                deflateurs = [1 / (1 + taux) ** maturité for maturité, taux in courbe["Taux courbe centrale"].items()]
                return pd.DataFrame({"Déflateur central": deflateurs}, index=courbe.index)

            def plot_ecart(deflateurs_centrals, deflateurs_simulés):
                annees = sorted(set(deflateurs_centrals.index).intersection(deflateurs_simulés.index))
                ecart_pct = ((deflateurs_simulés.loc[annees].values / deflateurs_centrals.loc[annees, "Déflateur central"].values) - 1) * 100

                plt.style.use("dark_background" if theme == "Sombre" else "default")
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(annees, ecart_pct, marker="o", color="#00ffe1")
                ax.axhline(0, color="gray", linestyle="--")
                ax.set_title("📊 Écart (%) entre déflateur central et simulé", fontsize=10)
                ax.set_xlabel("Maturité (années)")
                ax.set_ylabel("Écart (%)")
                ax.grid(True, linestyle="--", alpha=0.5)
                buf = io.BytesIO()
                fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
                buf.seek(0)
                st.image(buf, use_column_width=False)

            # === PIPELINE ===
            zc_1y = extraire_zc_1_year(df_zc)
            deflateurs_simulés = calcul_deflateurs_simulés(zc_1y)
            courbe_centrale = extraire_courbe_centrale(df_zc)
            deflateurs_centrals = calculer_deflateur_central(courbe_centrale)
            plot_ecart(deflateurs_centrals, deflateurs_simulés)

            return deflateurs_centrals, deflateurs_simulés

        deflateurs_centrals, deflateurs_simulés = analyse_taux_zc(df_zc)

        if affichage_tableaux:
            with st.expander("📋 Déflateurs centraux"):
                st.dataframe(deflateurs_centrals.style.format("{:.5f}").background_gradient(cmap="Blues"))
            with st.expander("📋 Déflateurs simulés (moyenne sur trajectoires)"):
                st.dataframe(deflateurs_simulés.to_frame(name="Déflateur simulé").style.format("{:.5f}").background_gradient(cmap="Purples"))

        # === TÉLÉCHARGEMENT ===
        st.sidebar.markdown("### 📥 Télécharger les résultats")

        def create_download(df):
            output = BytesIO()
            df.to_csv(output, sep=";", index=True)
            return output.getvalue()

        st.sidebar.download_button(
            label="⬇️ Déflateurs centraux (CSV)",
            data=create_download(deflateurs_centrals),
            file_name="deflateurs_centrals.csv",
            mime="text/csv"
        )
        st.sidebar.download_button(
            label="⬇️ Déflateurs simulés (CSV)",
            data=create_download(deflateurs_simulés.to_frame(name="Déflateur simulé")),
            file_name="deflateurs_simules.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"❌ Erreur lors de l’analyse du fichier : {e}")
else:
    st.info("📤 Veuillez téléverser un fichier CSV pour lancer l’analyse.")
