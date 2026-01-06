import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
import simplekml
from pdf2image import convert_from_bytes
from PIL import Image
import io
import zipfile
import kml2geojson
import cv2
import pytesseract
import numpy as np
import re
import base64  # <--- TAMBAHAN PENTING

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(layout="wide", page_title="Universal KMZ Digitizer")

# CSS untuk menyembunyikan menu Streamlit
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .block-container {padding-top: 1rem;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 2. FUNGSI BANTUAN (UTILITIES) ---

def pixel_to_latlon(x, y, width, height, bounds):
    """Konversi Pixel Gambar ke Koordinat GPS"""
    lat_min, lon_min = bounds[0]
    lat_max, lon_max = bounds[1]
    lat_range = lat_max - lat_min
    lon_range = lon_max - lon_min
    lat = lat_max - (y / height) * lat_range
    lon = lon_min + (x / width) * lon_range
    return lat, lon

def get_pole_regex(option_key):
    patterns = {
        "Angka+Huruf (Cth: 1A, 2B, 10C)": r'^[0-9]+[A-Z]$',
        "Huruf+Angka (Cth: P1, T01, A5)": r'^[A-Z]+[0-9]+$',
        "Format Kode (Cth: P-01, T-10)": r'^[A-Z]+-[0-9]+$',
        "Angka Saja (Cth: 1, 2, 10)": r'^[0-9]+$'
    }
    return patterns.get(option_key, r'^[0-9]+[A-Z]$')

def auto_detect(image_pil, bounds, config):
    img = np.array(image_pil)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    height, width = gray.shape

    with st.spinner("Membaca teks di gambar..."):
        custom_config = r'--oem 3 --psm 11'
        d = pytesseract.image_to_data(gray, config=custom_config, output_type=pytesseract.Output.DICT)
    
    detected_texts = []
    n_boxes = len(d['text'])
    for i in range(n_boxes):
        if int(d['conf'][i]) > 40:
            text = d['text'][i].strip()
            if text:
                cx = d['left'][i] + d['width'][i] // 2
                cy = d['top'][i] + d['height'][i] // 2
                detected_texts.append({'text': text, 'center': (cx, cy)})

    with st.spinner("Mencari simbol tiang..."):
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=20,
                                param1=50, param2=30, minRadius=3, maxRadius=20)
    
    results = []
    fat_kw = config['fat_keyword'] 
    fdt_kw = config['fdt_keyword'] 
    pole_pattern = config['pole_regex'] 

    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            label = "Unknown"
            obj_type = "TIANG/POLE"
            min_dist = 80
            
            for text_obj in detected_texts:
                tx, ty = text_obj['center']
                dist = np.sqrt((x - tx)**2 + (y - ty)**2)
                txt = text_obj['text']
                
                if dist < min_dist:
                    if fat_kw in txt:
                        obj_type = "FAT"
                        label = txt
                        min_dist = dist 
                    elif fdt_kw in txt:
                        obj_type = "FDT"
                        label = txt
                        min_dist = dist
                    elif re.match(pole_pattern, txt):
                        if obj_type == "TIANG/POLE": 
                            label = txt
                            min_dist = dist
            
            if label != "Unknown":
                lat, lon = pixel_to_latlon(x, y, width, height, bounds)
                results.append({
                    "type": obj_type,
                    "name": label,
                    "lat": lat,
                    "lon": lon
                })     
    return results

def load_kmz_to_geojson(uploaded_kmz):
    try:
        with zipfile.ZipFile(uploaded_kmz, 'r') as z:
            kml_filename = [f for f in z.namelist() if f.endswith('.kml')][0]
            with z.open(kml_filename) as kml_file:
                kml_content = kml_file.read()
        with open("temp_upload.kml", "wb") as f:
            f.write(kml_content)
        geojson_data = kml2geojson.main.convert("temp_upload.kml")
        return geojson_data[0] 
    except Exception as e:
        return None

# --- 3. MAIN APPLICATION ---

def main():
    st.title("🌐 WebGIS Digitizer Pro")
    
    with st.sidebar:
        st.header("1. File & Lokasi")
        uploaded_pdf = st.file_uploader("Upload PDF Area", type=['pdf'])
        
        with st.expander("📂 Overlay Eksisting (KMZ)", expanded=False):
            uploaded_kmz = st.file_uploader("Upload KMZ Lama", type=['kmz', 'kml'])
            existing_geojson = None
            if uploaded_kmz:
                if uploaded_kmz.name.endswith('.kmz'):
                    existing_geojson = load_kmz_to_geojson(uploaded_kmz)
                else:
                    with open("temp_upload.kml", "wb") as f:
                        f.write(uploaded_kmz.read())
                    existing_geojson = kml2geojson.main.convert("temp_upload.kml")[0]

        with st.expander("📍 Kalibrasi Peta (Georeference)", expanded=True):
            lat_center = st.number_input("Lat Center", value=-6.8800, format="%.5f")
            lon_center = st.number_input("Lon Center", value=109.1150, format="%.5f")
            zoom_scale = st.slider("Scale/Zoom PDF", 0.001, 0.020, 0.005, step=0.0001)
            opacity = st.slider("Transparansi", 0.0, 1.0, 0.6)
            
        st.divider()
        st.header("2. Standar Penamaan")
        fat_input = st.text_input("Kode Awal FAT", "FOT")
        fdt_input = st.text_input("Kode Awal FDT", "FDT")
        pole_opt = st.selectbox("Format Tiang", [
            "Angka+Huruf (Cth: 1A, 2B)", 
            "Huruf+Angka (Cth: P1, T01)",
            "Format Kode (Cth: P-01)",
            "Angka Saja (Cth: 1, 2)"
        ])
        
        config = {
            'fat_keyword': fat_input,
            'fdt_keyword': fdt_input,
            'pole_regex': get_pole_regex(pole_opt)
        }
        
        st.divider()
        run_auto = st.button("🚀 Jalankan Otomasi", type="primary")

    bounds = [
        [lat_center - zoom_scale, lon_center - zoom_scale],
        [lat_center + zoom_scale, lon_center + zoom_scale]
    ]
    
    col1, col2 = st.columns([3, 1])
    
    if 'auto_data' not in st.session_state:
        st.session_state['auto_data'] = []

    image_data = None
    if uploaded_pdf:
        try:
            images = convert_from_bytes(uploaded_pdf.read())
            image_data = images[0]
        except:
            st.error("Gagal load PDF.")

    if run_auto and image_data:
        results = auto_detect(image_data, bounds, config)
        st.session_state['auto_data'] = results
        st.success(f"Selesai! {len(results)} objek ditemukan.")

    with col1:
        m = folium.Map(location=[lat_center, lon_center], zoom_start=18)
        
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Satellite'
        ).add_to(m)
        
        if existing_geojson:
            folium.GeoJson(
                existing_geojson,
                name="Eksisting",
                style_function=lambda x: {'color': 'gray', 'weight': 2, 'dashArray': '5, 5'}
            ).add_to(m)

        # --- REVISI BAGIAN GAMBAR AGAR TIDAK ERROR ---
        if image_data:
            # 1. Simpan gambar ke buffer
            img_byte = io.BytesIO()
            image_data.save(img_byte, format='PNG')
            # 2. Encode ke Base64 (Teks) agar Folium bisa baca
            encoded_img = base64.b64encode(img_byte.getvalue()).decode()
            # 3. Buat Data URL
            img_url = f"data:image/png;base64,{encoded_img}"

            folium.raster_layers.ImageOverlay(
                image=img_url,  # Gunakan URL Base64, bukan bytes mentah
                bounds=bounds,
                opacity=opacity,
                name="PDF Area"
            ).add_to(m)
            
        for item in st.session_state['auto_data']:
            icon_color = "green"
            if item['type'] == "FAT": icon_color = "purple"
            elif item['type'] == "FDT": icon_color = "red"
                
            folium.Marker(
                [item['lat'], item['lon']],
                popup=f"<b>{item['name']}</b>",
                icon=folium.Icon(color=icon_color, icon="info-sign")
            ).add_to(m)
        
        draw = Draw(export=False)
        draw.add_to(m)
            
        st_folium(m, width="100%", height=700)

    with col2:
        st.subheader("📥 Download")
        if st.session_state['auto_data']:
            counts = {}
            for x in st.session_state['auto_data']:
                counts[x['type']] = counts.get(x['type'], 0) + 1
            st.write(counts)
            
            kml = simplekml.Kml()
            folders = {
                "TIANG/POLE": kml.newfolder(name="POLES"),
                "FAT": kml.newfolder(name="FAT"),
                "FDT": kml.newfolder(name="FDT")
            }
            
            for item in st.session_state['auto_data']:
                f = folders.get(item['type'], folders["TIANG/POLE"])
                p = f.newpoint(name=item['name'], coords=[(item['lon'], item['lat'])])
                if item['type'] == "FAT": 
                    p.style.iconstyle.color = simplekml.Color.purple
                    p.style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/paddle/purple-circle.png"
                elif item['type'] == "FDT": 
                    p.style.iconstyle.color = simplekml.Color.red
                    p.style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/paddle/red-circle.png"
                else: 
                    p.style.iconstyle.color = simplekml.Color.green
                    p.style.iconstyle.icon.href = "http://maps.google.com/mapfiles/kml/paddle/grn-circle.png"

            kmz_buf = io.BytesIO()
            kml.savekmz(kmz_buf)
            kmz_buf.seek(0)
            
            st.download_button(
                "DOWNLOAD .KMZ", 
                kmz_buf, 
                f"Design_Result.kmz", 
                "application/vnd.google-earth.kmz",
                type="primary"
            )
        else:
            st.info("Upload PDF & Klik 'Jalankan Otomasi' atau gambar manual.")

if __name__ == "__main__":
    main()
