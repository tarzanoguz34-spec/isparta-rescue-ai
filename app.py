from __future__ import annotations

import math
import random
from typing import Any
import base64
import folium
import networkx as nx
import osmnx as ox
import pandas as pd
import streamlit as st
from supabase import create_client
from streamlit_folium import st_folium

# ------------------------------------------------------------
# ISPARTA RESCUE AI — Streamlit başlangıç sürümü
# Eğitim amaçlı simülasyondur; gerçek acil müdahale için kullanılamaz.
# ------------------------------------------------------------

st.set_page_config(
    page_title="ISPARTA RESCUE AI",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded",
)
# ISPARTA RESCUE AI — Arka plan tasarımı
with open(".devcontainer/isparta_arka_plan.png.png", "rb") as image_file:
    background_image = base64.b64encode(
        image_file.read()
    ).decode()

st.markdown(
    f"""
    <style>
    .stApp {{
        background-image:
            linear-gradient(
                rgba(3, 10, 28, 0.35),
                rgba(3, 10, 28, 0.50)
            ),
            url("data:image/png;base64,{background_image}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    [data-testid="stHeader"] {{
        background: rgba(0, 0, 0, 0);
    }}

    .block-container {{
        padding-top: 2rem;
    }}
    </style>
    """,
    unsafe_allow_html=True
)
def get_supabase_client():
    if "supabase_client" not in st.session_state:
        st.session_state["supabase_client"] = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"]
        )

    return st.session_state["supabase_client"]


try:
    supabase = get_supabase_client()
    supabase_configured = True
except Exception as e:
    supabase = None
    supabase_configured = False
    st.error(f"Supabase bağlantı hatası: {e}")
    st.stop()


# ------------------------------------------------------------
# KULLANICI KAYIT VE GİRİŞ EKRANI
# ------------------------------------------------------------

st.markdown("""
<style>
.brand-header {
    text-align: center;
    padding: 25px 15px 20px 15px;
    background: rgba(5, 15, 38, 0.72);
    border: 1px solid rgba(255,255,255,0.22);
    border-radius: 18px;
    margin-bottom: 22px;
    backdrop-filter: blur(8px);
}
.sponsor {
    color: #fbbf24;
    font-size: 15px;
    font-weight: 800;
    letter-spacing: 3px;
}
.brand-title {
    color: white;
    font-size: 38px;
    font-weight: 900;
    margin: 12px 0 5px 0;
    text-shadow: 0 3px 15px #000;
}
.brand-subtitle {
    color: #dbeafe;
    font-size: 16px;
}
</style>

<div class="brand-header">
    <div class="sponsor">IŞIKKENT AİHL SPONSORLUĞUNDA</div>
    <div class="brand-title">🚑 ISPARTA RESCUE AI</div>
    <div class="brand-subtitle">
        Daha Güvenli Bir Isparta İçin...
    </div>
</div>
""", unsafe_allow_html=True)

st.caption("Eğitim amaçlı afet müdahale simülasyonu")
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
st.markdown("""
<style>
div[data-testid="stTabs"] {
    background: rgba(5, 15, 38, 0.82);
    padding: 22px;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.20);
    box-shadow: 0 8px 30px rgba(0,0,0,0.35);
}

div[data-testid="stTextInput"] label {
    color: white !important;
    font-weight: 600;
}

div[data-testid="stButton"] button {
    background: linear-gradient(90deg, #b91c1c, #1d4ed8);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: bold;
    width: 100%;
    min-height: 45px;
}

div[data-testid="stButton"] button:hover {
    border: 1px solid white;
    color: white;
}
</style>
""", unsafe_allow_html=True)
if st.session_state["user_id"] is None:
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])

    with tab1:
        st.subheader("Hesabına giriş yap")
        login_email = st.text_input("E-posta", key="login_email")
        login_password = st.text_input(
            "Şifre", type="password", key="login_password"
        )

        if st.button("Giriş Yap", key="login_button"):
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": login_email,
                    "password": login_password
                })

                st.session_state["user_id"] = response.user.id
                st.success("Giriş başarılı!")
                st.rerun()

            except Exception:
                st.error("Giriş başarısız. E-posta ve şifreni kontrol et.")

    with tab2:
        st.subheader("Yeni hesap oluştur")
        signup_email = st.text_input("E-posta adresi", key="signup_email")
        signup_password = st.text_input(
            "Şifre", type="password", key="signup_password"
        )

        if st.button("Kayıt Ol", key="signup_button"):
            try:
                response = supabase.auth.sign_up({
                    "email": signup_email,
                    "password": signup_password
                })

                if response.session is not None:
                    st.session_state["user_id"] = response.user.id
                    st.success("Hesabın oluşturuldu!")
                    st.rerun()
                else:
                    st.info(
                        "Kayıt oluşturuldu. E-posta adresine gelen "
                        "doğrulama bağlantısını kontrol et."
                    )

           except Exception as e:
    st.error(f"Kayıt hatası: {e}")

    st.stop()


st.sidebar.success("Giriş yapıldı")
st.sidebar.write(f"Kullanıcı ID: {st.session_state['user_id']}")

if st.sidebar.button("Çıkış Yap"):
    try:
        supabase.auth.sign_out()
    finally:
        st.session_state["user_id"] = None
        st.rerun()


CENTER = (37.7648, 30.5566)  # Isparta şehir merkezi (varsayılan harita odağı)

TEAM_OFFSETS = [
    (-0.012, -0.014),
    ( 0.012, -0.014),
    (-0.012,  0.014),
    ( 0.012,  0.014),
]
TEAM_NAMES = ["Ekip 1", "Ekip 2", "Ekip 3", "Ekip 4"]
TEAM_COLORS = ["blue", "green", "purple", "darkred"]


@st.cache_resource(show_spinner=False)
def load_graph(network_type: str, dist_m: int) -> nx.MultiDiGraph:
    """Download and cache an OSM road/pedestrian network around Isparta."""
    ox.settings.use_cache = True
    ox.settings.log_console = False
    ox.settings.timeout = 180
    return ox.graph_from_point(
        CENTER,
        dist=dist_m,
        network_type=network_type,
        simplify=True,
    )


def nearest_node(graph: nx.MultiDiGraph, lat: float, lon: float) -> Any:
    return ox.distance.nearest_nodes(graph, X=lon, Y=lat)


def route_length(graph: nx.MultiDiGraph, route: list) -> float:
    total = 0.0
    for u, v in zip(route[:-1], route[1:]):
        data = graph.get_edge_data(u, v)
        if not data:
            continue
        total += min(float(d.get("length", 0)) for d in data.values())
    return total


def route_coords(graph: nx.MultiDiGraph, route: list) -> list[tuple[float, float]]:
    coords = []
    for node in route:
        data = graph.nodes[node]
        coords.append((float(data["y"]), float(data["x"])))
    return coords


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(h))


def team_points(radius_km: float) -> list[tuple[float, float]]:
    # Dört ekip, Isparta merkezinin çevresinde varsayımsal konumlandırılır.
    lat_scale = radius_km / 111.0
    lon_scale = radius_km / (111.0 * math.cos(math.radians(CENTER[0])))
    return [
        (CENTER[0] + dy * lat_scale / 0.012, CENTER[1] + dx * lon_scale / 0.014)
        for dy, dx in TEAM_OFFSETS
    ]


def add_route_layer(m: folium.Map, graph: nx.MultiDiGraph, route: list,
                    color: str, label: str, weight: int = 5) -> None:
    folium.PolyLine(
        route_coords(graph, route),
        color=color,
        weight=weight,
        opacity=0.9,
        tooltip=label,
    ).add_to(m)


def build_map(incident: tuple[float, float], teams: list[tuple[float, float]],
              routes: list[dict] | None = None, show_teams: bool = True) -> folium.Map:
    m = folium.Map(location=incident, zoom_start=13, control_scale=True, tiles="OpenStreetMap")
    folium.Marker(
        incident,
        tooltip="Seçilen simülasyon afet noktası",
        popup="Afet noktası (varsayımsal)",
        icon=folium.Icon(color="red", icon="warning-sign"),
    ).add_to(m)

    if show_teams:
        for i, point in enumerate(teams):
            folium.Marker(
                point,
                tooltip=TEAM_NAMES[i],
                popup=f"{TEAM_NAMES[i]} — varsayımsal konum",
                icon=folium.Icon(color=TEAM_COLORS[i], icon="plus-sign"),
            ).add_to(m)

    for item in routes or []:
        add_route_layer(m, item["graph"], item["route"], item["color"], item["label"])
    folium.LayerControl().add_to(m)
    return m


st.markdown(
    """
    <div style="padding: 0.4rem 0 0.8rem 0">
      <div style="font-size:0.82rem;letter-spacing:0.18em;color:#60a5fa;font-weight:700">
        ISPARTA · AFET VE KURTARMA SİMÜLASYONU
      </div>
      <h1 style="margin:0.15rem 0 0 0">🚑 ISPARTA RESCUE AI</h1>
      <p style="color:#94a3b8;margin-top:0.3rem">
        Harita tabanlı ekip erişimi, rota optimizasyonu ve senaryo analizi
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.warning(
    "Bu uygulama eğitim ve proje gösterimi için hazırlanmış bir simülasyondur. "
    "Veriler, yol durumu ve sonuçlar gerçek zamanlı doğrulanmadığından gerçek acil müdahalede kullanılmamalıdır."
)

with st.sidebar:
    st.header("⚙️ Simülasyon ayarları")
    radius = st.slider("Ekiplerin merkezden varsayımsal uzaklığı (km)", 0.5, 4.0, 1.8, 0.1)
    network_dist = st.select_slider("Yol ağı indirme alanı", options=[3000, 4000, 5000, 6000, 7000], value=5000,
                                    format_func=lambda x: f"{x/1000:.0f} km")
    network_mode = st.radio("Ulaşım ağı", ["Araç", "Yaya"], horizontal=True)
    st.caption("Haritaya tıklayarak afet noktasını değiştirebilirsin.")
    if st.button("Varsayılan afet noktasına dön", use_container_width=True):
        st.session_state["incident"] = CENTER
        st.rerun()

teams = team_points(radius)
if "incident" not in st.session_state:
    st.session_state["incident"] = (CENTER[0] + 0.003, CENTER[1] + 0.002)
incident = st.session_state["incident"]

# First map is interactive and does not require downloading road data.
left, right = st.columns([1.55, 1])
with left:
    st.subheader("🗺️ Isparta operasyon haritası")
    st.caption("Harita üzerinde bir noktaya tıklayarak varsayımsal afet konumunu seç.")
    base_map = build_map(incident, teams)
    map_state = st_folium(base_map, height=560, use_container_width=True, returned_objects=["last_clicked"])
    if map_state and map_state.get("last_clicked"):
        clicked = map_state["last_clicked"]
        new_point = (float(clicked["lat"]), float(clicked["lng"]))
        if haversine_m(new_point, incident) > 15:
            st.session_state["incident"] = new_point
            incident = new_point
            st.rerun()

with right:
    st.subheader("📍 Senaryo özeti")
    st.metric("Kurtarma ekibi", "4", help="Dört ekip konumu simülasyon için varsayılmıştır.")
    st.metric("Afet noktası", f"{incident[0]:.5f}, {incident[1]:.5f}")
    st.metric("Ekiplerin merkezden uzaklığı", f"{radius:.1f} km")
    st.markdown("**Ekip konumları**")
    for name, point in zip(TEAM_NAMES, teams):
        st.write(f"• **{name}:** {point[0]:.4f}, {point[1]:.4f}")

st.divider()
tab_route, tab_closure, tab_risk, tab_coverage = st.tabs(
    ["🧭 Ekip ve rota analizi", "🚧 Yol kapanması", "⚠️ Risk analizi", "🧩 Ekip bölgeleri"]
)

@st.cache_resource(show_spinner=False)
def get_network(mode: str, dist: int):
    network_type = "drive" if mode == "Araç" else "walk"
    return load_graph(network_type, dist)

with tab_route:
    st.subheader("En yakın ekibin yol ağına göre belirlenmesi")
    st.write("Hesaplama, seçilen ulaşım ağı üzerinde OpenStreetMap yol verisiyle yapılır.")
    if st.button("Rota analizini çalıştır", type="primary", key="route_run"):
        try:
            with st.spinner("Isparta yol ağı alınıyor ve rotalar hesaplanıyor... İlk çalıştırma biraz sürebilir."):
                G = get_network(network_mode, network_dist)
                target_node = nearest_node(G, *incident)
                rows, route_layers = [], []
                for i, team in enumerate(teams):
                    start_node = nearest_node(G, *team)
                    try:
                        route = nx.shortest_path(G, start_node, target_node, weight="length")
                        distance = route_length(G, route)
                        rows.append({"Ekip": TEAM_NAMES[i], "Mesafe (m)": round(distance, 1),
                                     "Düğüm sayısı": len(route), "Durum": "Rota bulundu"})
                        route_layers.append({"graph": G, "route": route, "color": TEAM_COLORS[i],
                                             "label": f"{TEAM_NAMES[i]} — {distance:.0f} m"})
                    except (nx.NetworkXNoPath, nx.NodeNotFound):
                        rows.append({"Ekip": TEAM_NAMES[i], "Mesafe (m)": None,
                                     "Düğüm sayısı": None, "Durum": "Bağlantı bulunamadı"})
                st.session_state["route_rows"] = rows
                st.session_state["route_layers"] = route_layers
                st.session_state["active_graph"] = G
                st.session_state["active_mode"] = network_mode
        except Exception as exc:
            st.error(f"Yol ağı alınamadı veya rota hesaplanamadı: {exc}")
            st.info("İnternet bağlantısını kontrol edip yeniden deneyebilirsin. OpenStreetMap hizmeti geçici olarak yanıt vermiyor olabilir.")

    if "route_rows" in st.session_state and st.session_state.get("active_mode") == network_mode:
        df = pd.DataFrame(st.session_state["route_rows"])
        st.dataframe(df, use_container_width=True, hide_index=True)
        valid = df.dropna(subset=["Mesafe (m)"])
        if not valid.empty:
            best = valid.sort_values("Mesafe (m)").iloc[0]
            st.success(f"Bu simülasyonda en kısa yol ağı mesafesi: **{best['Ekip']} — {best['Mesafe (m)']:.1f} m**")
            route_map = build_map(incident, teams, st.session_state.get("route_layers", []))
            st_folium(route_map, height=480, use_container_width=True, key="route_map")
        st.caption("Mesafeler yol ağı uzunluğudur; trafik, ekip kapasitesi ve gerçek saha koşulları hesaba katılmaz.")

with tab_closure:
    st.subheader("Tek bir yol kesiminin kapanması senaryosu")
    st.write("Önce rota analizini çalıştır. Ardından seçilen ekibin rotasındaki bir yol kesimi geçici olarak kapatılarak alternatif aranır.")
    if "route_layers" not in st.session_state or not st.session_state.get("route_layers"):
        st.info("Önce “Ekip ve rota analizi” sekmesinde rota hesapla.")
    else:
        route_layers = st.session_state["route_layers"]
        chosen_label = st.selectbox("Kapatma senaryosu için ekip", [x["label"] for x in route_layers])
        chosen = next(x for x in route_layers if x["label"] == chosen_label)
        route = chosen["route"]
        if len(route) >= 3:
            edge_index = st.slider("Kapatılacak yol kesimi (rota üzerindeki sıra)", 1, len(route)-2, max(1, len(route)//2))
            if st.button("Yol kapanmasını simüle et", key="closure_run"):
                G = chosen["graph"].copy()
                u, v = route[edge_index-1], route[edge_index]
                for a, b in [(u, v), (v, u)]:
                    if G.has_edge(a, b):
                        G.remove_edges_from([(a, b, k) for k in list(G[a][b].keys())])
                try:
                    alternative = nx.shortest_path(G, route[0], route[-1], weight="length")
                    normal_m = route_length(chosen["graph"], route)
                    alt_m = route_length(G, alternative)
                    st.session_state["closure_result"] = {
                        "normal": normal_m, "alternative": alt_m,
                        "route": alternative, "graph": G, "team": chosen_label,
                    }
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    st.session_state["closure_result"] = {"error": "Bu yol kesimi kapatıldığında alternatif bağlantı bulunamadı."}
        result = st.session_state.get("closure_result")
        if result:
            if "error" in result:
                st.warning(result["error"])
            else:
                delta = result["alternative"] - result["normal"]
                c1, c2, c3 = st.columns(3)
                c1.metric("Normal rota", f"{result['normal']:.0f} m")
                c2.metric("Alternatif rota", f"{result['alternative']:.0f} m")
                c3.metric("Mesafe farkı", f"{delta:+.0f} m", f"{(delta/result['normal']*100):+.1f}%")
                closure_map = build_map(incident, teams, [
                    {"graph": result["graph"], "route": result["route"], "color": "orange",
                     "label": "Alternatif rota"}
                ])
                st_folium(closure_map, height=440, use_container_width=True, key="closure_map")
        else:
            st.caption("Henüz kapanma sonucu yok.")

with tab_risk:
    st.subheader("Risk ağırlıklı rota denemesi")
    st.write("Bu sürümde yol kesimlerine rastgele ve tekrarlanabilir örnek risk puanları atanır. Bu puanlar gerçek afet tehlikesi verisi değildir.")
    if "route_layers" not in st.session_state or not st.session_state.get("route_layers"):
        st.info("Önce rota analizi çalıştır.")
    else:
        route_layers = st.session_state["route_layers"]
        chosen_label = st.selectbox("Risk analizi yapılacak ekip", [x["label"] for x in route_layers], key="risk_team")
        chosen = next(x for x in route_layers if x["label"] == chosen_label)
        if st.button("Risk ağırlıklı rotayı hesapla", key="risk_run"):
            G = chosen["graph"].copy()
            random.seed(42)
            for u, v, k, data in G.edges(keys=True, data=True):
                risk = random.random()
                data["risk"] = risk
                data["risk_cost"] = float(data.get("length", 1)) * (1 + risk * 4)
            try:
                risk_route = nx.shortest_path(G, chosen["route"][0], chosen["route"][-1], weight="risk_cost")
                st.session_state["risk_result"] = {
                    "graph": G, "route": risk_route,
                    "normal": chosen["route"],
                    "normal_m": route_length(chosen["graph"], chosen["route"]),
                    "risk_m": route_length(G, risk_route),
                }
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                st.error("Risk ağırlıklı rota bulunamadı.")
        result = st.session_state.get("risk_result")
        if result:
            a, b = st.columns(2)
            a.metric("Normal rota uzunluğu", f"{result['normal_m']:.0f} m")
            b.metric("Risk ağırlıklı rota uzunluğu", f"{result['risk_m']:.0f} m")
            risk_map = build_map(incident, teams, [
                {"graph": result["graph"], "route": result["normal"], "color": "blue", "label": "Normal rota"},
                {"graph": result["graph"], "route": result["route"], "color": "orange", "label": "Risk ağırlıklı rota"},
            ])
            st_folium(risk_map, height=440, use_container_width=True, key="risk_map")

with tab_coverage:
    st.subheader("Dört ekibin varsayımsal kapsama bölgeleri")
    st.write("Voronoi bölgelemesi, her konumu en yakın ekip noktasına göre ayıran geometrik bir gösterimdir. Yol ağına dayalı gerçek hizmet alanı değildir.")
    try:
        import numpy as np
        import matplotlib.pyplot as plt
        from scipy.spatial import Voronoi
        from shapely.geometry import Polygon, box

        # Yerel düzlemde yaklaşık kilometre koordinatları kullanılır.
        lat0, lon0 = CENTER
        xy = np.array([
            ((lon-lon0) * 111.0 * math.cos(math.radians(lat0)), (lat-lat0) * 111.0)
            for lat, lon in teams
        ])
        pad = radius * 2.2
        bounds = box(-pad, -pad, pad, pad)
        vor = Voronoi(xy)
        fig, ax = plt.subplots(figsize=(8, 6))
        region_colors = ["#2563eb", "#16a34a", "#9333ea", "#dc2626"]
        for i, region_index in enumerate(vor.point_region):
            region = vor.regions[region_index]
            if region and -1 not in region:
                poly = Polygon(vor.vertices[region]).intersection(bounds)
                if not poly.is_empty:
                    x, y = poly.exterior.xy
                    ax.fill(x, y, alpha=0.20, color=region_colors[i], label=TEAM_NAMES[i])
        ax.scatter(xy[:, 0], xy[:, 1], marker="^", s=100, c=region_colors, edgecolor="black")
        for i, (x, y) in enumerate(xy):
            ax.annotate(TEAM_NAMES[i], (x, y), xytext=(5, 5), textcoords="offset points")
        ax.set_xlim(-pad, pad)
        ax.set_ylim(-pad, pad)
        ax.set_xlabel("Doğu-Batı (yaklaşık km)")
        ax.set_ylabel("Kuzey-Güney (yaklaşık km)")
        ax.set_title("ISPARTA RESCUE AI — Varsayımsal Voronoi ekip bölgeleri")
        ax.grid(alpha=0.2)
        ax.legend()
        st.pyplot(fig)
        plt.close(fig)
    except Exception as exc:
        st.error(f"Bölgeleme çizilemedi: {exc}")

st.divider()
st.caption("ISPARTA RESCUE AI · İlk Streamlit prototipi · Açık harita verisi: OpenStreetMap · Simülasyon amaçlıdır.")
