import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def analyse_taux_zc(df_zc):
    def extraire_zc_1_year(df_zc):
        df_1y = df_zc[df_zc["Maturité"] == 1].copy()
        df_1y = df_1y.drop(columns=["Maturité"])
        df_1y = df_1y.set_index("TRAJECTOIRE")
        df_1y = df_1y.sort_index()
        return df_1y

    def calcul_deflateurs_simulés(zc_1y):
        deflateurs = pd.DataFrame(index=zc_1y.index, columns=zc_1y.columns)
        for traj in zc_1y.index:
            for t in zc_1y.columns:
                taux = zc_1y.loc[traj, t]
                if t == 0:
                    deflateurs.loc[traj, t] = 1 / (1 + taux)
                else:
                    deflateurs.loc[traj, t] = deflateurs.loc[traj, t - 1] * (1 / (1 + taux))
        deflateurs = deflateurs.astype(float)
        deflateurs.index = deflateurs.index + 1
        deflateurs = deflateurs.iloc[:-1]
        return deflateurs

    def extraire_courbe_centrale(df_zc):
        df_filtré = df_zc[(df_zc["TRAJECTOIRE"] == 1) & (df_zc["Maturité"].between(1, 50))].copy()
        courbe_centrale = df_filtré[["Maturité", 0]].set_index("Maturité").sort_index()
        courbe_centrale.columns = ["Taux courbe centrale"]
        return courbe_centrale

    def calculer_deflateur_central(courbe_centrale):
        deflateurs = [1 / (1 + taux) ** Maturité for Maturité, taux in courbe_centrale["Taux courbe centrale"].items()]
        return pd.DataFrame({"Déflateur central": deflateurs}, index=courbe_centrale.index)

    def plot_ecart_pourcentage_par_maturité(deflateurs_centrals, df_deflateurs_output):
        if isinstance(deflateurs_centrals, pd.Series):
            deflateurs_centrals = deflateurs_centrals.to_frame(name="Déflateur central")

        if isinstance(df_deflateurs_output, pd.Series):
            df_deflateurs_output = df_deflateurs_output.to_frame().T

        df_deflateurs_output.columns = df_deflateurs_output.columns.astype(int)
        df_deflateurs_output = df_deflateurs_output.sort_index(axis=1)

        années = sorted(set(deflateurs_centrals.index).intersection(df_deflateurs_output.columns))

        deflateur_central = deflateurs_centrals.loc[années, "Déflateur central"].values
        deflateur_simulé = df_deflateurs_output[années].mean().values

        ecart_pct = ((deflateur_simulé / deflateur_central) - 1) * 100

        plt.figure(figsize=(10, 5))
        plt.plot(années, ecart_pct, marker="o", color="teal")
        plt.axhline(0, color="gray", linestyle="--")
        plt.title("Écart en % de la martingalité (déflateur Output vs Input)")
        plt.xlabel("Maturité (années)")
        plt.ylabel("Écart (%)")
        plt.grid(True)
        plt.tight_layout()
        st.pyplot(plt)

    # Pipeline
    zc_1year = extraire_zc_1_year(df_zc)
    deflateurs_simulés = calcul_deflateurs_simulés(zc_1year)
    courbe_centrale = extraire_courbe_centrale(df_zc)
    deflateurs_centrals = calculer_deflateur_central(courbe_centrale)
    plot_ecart_pourcentage_par_maturité(deflateurs_centrals, deflateurs_simulés)

    return deflateurs_centrals, deflateurs_simulés

# Interface utilisateur
st.title("Analyse des Taux Zéro-Coupon")

uploaded_file = st.file_uploader("Téléversez un fichier CSV contenant les taux zéro-coupon", type=["csv"])

if uploaded_file is not None:
    df_zc = pd.read_csv(uploaded_file, encoding="ISO-8859-1")

    deflateurs_centrals, deflateurs_simulés = analyse_taux_zc(df_zc)

    st.subheader("Déflateurs Centraux")
    st.dataframe(deflateurs_centrals)

    st.subheader("Déflateurs Simulés")
    st.dataframe(deflateurs_simulés)
