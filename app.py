import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from rdf_python_model_2 import RDFPositionError  # rename to match your file





st.set_page_config(page_title="Direction Finding RMS accuracy and Sensor Geometry Calculator", layout="wide")

st.title("📡 Direction Finding RMS accuracy and Sensor Geometry Calculator")

# --- Sidebar controls ---
st.sidebar.image("assets/logo.png", width=150)
st.sidebar.markdown(
    """
    <a href="https://commsaudit.com" target="_blank">
        <img src="https://github.com/makingithardertohide/rdf/assets/logo.png" width="180">
    </a>
    """,
    unsafe_allow_html=True
)
st.sidebar.markdown("[CommsAudit](https://commsaudit.com)")
st.sidebar.header("Controls")

s1_x = st.sidebar.slider("Sensor 1 X (km)", -50.0, 50.0, -5.0, 0.1) * 1000
s1_y = st.sidebar.slider("Sensor 1 Y (km)", -50.0, 50.0, 0.0, 0.1) * 1000
s2_x = st.sidebar.slider("Sensor 2 X (km)", -50.0, 50.0, 5.0, 0.1) * 1000
s2_y = st.sidebar.slider("Sensor 2 Y (km)", -50.0, 50.0, 0.0, 0.1) * 1000
t_x = st.sidebar.slider("Target X (km)", -50.0, 50.0, 0.0, 0.1) * 1000
t_y = st.sidebar.slider("Target Y (km)", 0.0, 50.0, 8.0, 0.1) * 1000
bearing_error = st.sidebar.slider("Bearing Error (deg)", 0.1, 10.0, 2.0, 0.1)

# --- Compute model ---
model = RDFPositionError(
    sensor1_pos=(s1_x, s1_y),
    sensor2_pos=(s2_x, s2_y),
    target_pos=(t_x, t_y),
    bearing_error_deg=bearing_error
)

# --- Results column ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 Results")
    st.json(model.get_results())

    # Excel Export
    if st.button("📥 Export results to Excel"):
        filename = "rdf_results.xlsx"
        model.export_to_excel(filename)
        with open(filename, "rb") as f:
            st.download_button("Download Excel File", f, filename)

# --- Plot column ---
with col2:
    st.subheader("📡 Geometry Plot")

    fig, ax = plt.subplots(figsize=(7, 7))

    # Plot sensors and target
    ax.plot(model.s1[0], model.s1[1], "bs", markersize=10, label="Sensor 1")
    ax.plot(model.s2[0], model.s2[1], "rs", markersize=10, label="Sensor 2")
    ax.plot(model.target[0], model.target[1], "go", markersize=10, label="Target")

    # Baseline
    ax.plot(
        [model.s1[0], model.s2[0]],
        [model.s1[1], model.s2[1]],
        "k--", alpha=0.6
    )

    # Error circle
    circle = Circle(model.target, model.max_position_error,
                    fill=True, alpha=0.2, color="orange")
    ax.add_patch(circle)

    # Labels
    ax.text(model.s1[0], model.s1[1], " S1", color="blue")
    ax.text(model.s2[0], model.s2[1], " S2", color="red")
    ax.text(model.target[0], model.target[1], " Target", color="green")

    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.set_title("RDF Geometry")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")

    st.pyplot(fig)









