import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from PIL import Image

st.set_page_config(layout="wide")

# =========================
# FORMATACAO
# =========================
def fmt_num(x):
    return f"{int(x):,}".replace(",", ".")

def fmt_pct(x):
    return f"{x:.4f}%"

# =========================
# CSS CENTRALIZACAO
# =========================
st.markdown("""
<style>
thead tr th {text-align: center !important;}
tbody tr td {text-align: center !important;}
</style>
""", unsafe_allow_html=True)

# =========================
# LOGIN
# =========================
if "logged" not in st.session_state:
    st.session_state.logged = False

if not st.session_state.logged:
    st.title("🔐 Acesso ao Dashboard")
    user = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if user == "gabriel@bayer.com" and password == "bayer123":
            st.session_state.logged = True
            st.rerun()
        else:
            st.error("Acesso negado")

    st.stop()

# =========================
# CONFIG
# =========================
PRECO_SACA = 850

# =========================
# LOGO
# =========================
logo = Image.open("Agroceres.png")
c1, c2, c3 = st.columns([1,2,1])
with c2:
    st.image(logo, width=250)

# =========================
# LOAD
# =========================
df = pd.read_excel("base_agro_demanda.xlsx", sheet_name="PIPELINE_DEMANDA")
area = pd.read_excel("base_agro_demanda.xlsx", sheet_name="MUNICIPIOS_BASE")

# =========================
# TRATAMENTO
# =========================
df = df[df["Cultura"] == "Milho"].copy()
area = area[area["Cultura"] == "Milho"]

df["Status"] = df["Status"].str.strip().str.capitalize()
df["Sacas"] = df["Area_ha"]
df["Receita"] = df["Sacas"] * PRECO_SACA

if "UF" not in df.columns:
    df["UF"] = "PR"

# =========================
# FILTROS
# =========================
st.sidebar.header("Filtros")

rtv = st.sidebar.multiselect("RTV", df["RTV"].unique())
cliente = st.sidebar.multiselect("Cliente", df["Cliente_ID"].unique())
municipio = st.sidebar.multiselect("Município", df["Municipio"].unique())
status = st.sidebar.multiselect("Pipeline", df["Status"].unique())
uf = st.sidebar.multiselect("UF", df["UF"].unique())

if rtv: df = df[df["RTV"].isin(rtv)]
if cliente: df = df[df["Cliente_ID"].isin(cliente)]
if municipio: df = df[df["Municipio"].isin(municipio)]
if status: df = df[df["Status"].isin(status)]
if uf: df = df[df["UF"].isin(uf)]

# =========================
# MARKET SIZE AJUSTADO (COM FILTRO)
# =========================
area_filtrada = area.copy()

if municipio:
    area_filtrada = area_filtrada[area_filtrada["Municipio"].isin(municipio)]

area_total = area_filtrada["Area_ha"].sum()

# =========================
# KPI
# =========================
total_sacas = df["Sacas"].sum()
total_receita = df["Receita"].sum()
clientes = df["Cliente_ID"].nunique()

ticket = total_receita / clientes if clientes else 0
market_share = (total_sacas / area_total) * 100 if area_total > 0 else 0

st.title("📊 Inteligência Comercial - Sementes de Milho")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("🌽 Sacas", fmt_num(total_sacas))
c2.metric("💰 Receita", fmt_num(total_receita))
c3.metric("👥 Clientes", clientes)
c4.metric("🎯 Ticket Médio", fmt_num(ticket))
c5.metric("📊 Market Share", fmt_pct(market_share))

# =========================
# PIPELINE
# =========================
st.subheader("🔄 Pipeline")

pipe = df.groupby("Status").agg({
    "Sacas":"sum",
    "Cliente_ID":"nunique"
}).reset_index()

st.dataframe(pipe, use_container_width=True)

fig = px.bar(pipe, x="Sacas", y="Status", orientation="h", text="Sacas")
st.plotly_chart(fig, use_container_width=True)

# =========================
# RANKING CLIENTES
# =========================
st.subheader("🏆 Ranking Clientes")

ranking = df.groupby(["Cliente_ID","Municipio"]).agg({
    "Sacas":"sum",
    "Receita":"sum"
}).reset_index()

ranking["Customer Share (%)"] = (ranking["Sacas"] / total_sacas) * 100

st.dataframe(ranking, use_container_width=True)

# =========================
# PERFORMANCE RTV
# =========================
st.subheader("📈 Performance RTV")

perf = df.groupby("RTV").agg({
    "Sacas":"sum"
}).reset_index()

perf["Market Share (%)"] = (perf["Sacas"] / total_sacas) * 100

st.dataframe(perf, use_container_width=True)

# =========================
# ROI CORRIGIDO (SEM RANDOM)
# =========================
st.subheader("💸 ROI por Cliente")

roi = df.groupby("Cliente_ID").agg({
    "Sacas":"sum"
}).reset_index()

roi["Receita"] = roi["Sacas"] * PRECO_SACA

# investimento fixo (defensável)
roi["Investimento"] = 10 * PRECO_SACA

roi["Lucro"] = roi["Receita"] - roi["Investimento"]
roi["ROI (%)"] = (roi["Lucro"] / roi["Investimento"]) * 100

st.dataframe(roi, use_container_width=True)

# =========================
# OPORTUNIDADES
# =========================
st.subheader("⚠️ Oportunidades")

op = df[df["Status"]!="Convertido"]

op_group = op.groupby("Municipio")["Sacas"].sum().reset_index()

st.dataframe(op_group, use_container_width=True)

# =========================
# CLIENTES POR MUNICIPIO
# =========================
st.subheader("📌 Clientes por Município")

clientes_mun = op.groupby("Municipio")["Cliente_ID"].apply(list).reset_index()

st.dataframe(clientes_mun, use_container_width=True)

# =========================
# MAPA COM LEGENDA
# =========================
st.subheader("🗺️ Mapa")

coords = {
    "Campo Mourão": (-24.046, -52.378),
    "Mamborê": (-24.323, -52.529),
    "Goioerê": (-24.183, -53.025),
    "Ubiratã": (-24.539, -52.986),
    "Cascavel": (-24.955, -53.455),
    "Toledo": (-24.724, -53.743)
}

mapa = folium.Map(location=[-24.5, -53], zoom_start=6)

for _, row in df.iterrows():
    lat, lon = coords.get(row["Municipio"], (None, None))
    if lat is None: continue

    cor = "green" if row["Status"]=="Convertido" else "orange" if row["Status"]=="Lado a lado" else "red"

    folium.CircleMarker(location=[lat, lon], radius=6, color=cor, fill=True).add_to(mapa)

legend = """
<div style="position: fixed; bottom: 50px; left: 50px; background:white; padding:10px;">
<b>Legenda</b><br>
🟢 Convertido<br>
🟠 Lado a lado<br>
🔴 Prospecção
</div>
"""
mapa.get_root().html.add_child(folium.Element(legend))

st_folium(mapa, width=1200, height=500)