import streamlit as st
from PIL import Image
import numpy as np
import pandas as pd
import io
import random

# ============================================================
# CONFIGURATION GÉNÉRALE DE LA PAGE STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Générateur de Nuage de Collaborateurs",
    layout="wide"
)

# ============================================================
# STYLE CSS PERSONNALISÉ (NE MODIFIE PAS L'UI FONCTIONNELLE)
# ============================================================

st.markdown("""
<style>
div.stButton > button {
    background-color: #FFC107 !important;
    color: #003366 !important;
    border: 2px solid #003366 !important;
    font-weight: bold !important;
    border-radius: 5px;
    height: 3em !important;
    transition: all 0.3s ease;
}
div.stButton > button:hover {
    background-color: #0000FF !important;
    color: #FFC107 !important;
    transform: scale(1.02);
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# FONCTIONS UTILITAIRES IMAGE
# ============================================================


def convert_to_rgba(pil_image):
    """
    Convertit une image PIL en mode RGBA si nécessaire.

    Objectif :
    - Garantir la présence d'un canal alpha
    - Permettre le collage avec transparence sur le canvas final

    :param pil_image: PIL.Image.Image
    :return: PIL.Image.Image en RGBA
    """
    return pil_image.convert("RGBA") if pil_image.mode != "RGBA" else pil_image


def make_transparent(pil_image, tolerance=200):
    """
    Rend les pixels clairs (proches du blanc) transparents.

    Utilisé principalement pour les logos JPEG ne contenant
    pas de canal alpha natif.

    :param pil_image: Image PIL
    :param tolerance: seuil de détection du blanc
    :return: Image PIL RGBA avec fond transparent
    """
    rgba_image = convert_to_rgba(pil_image)
    pixels = rgba_image.getdata()

    new_pixels = [
        (255, 255, 255, 0)
        if px[0] > tolerance and px[1] > tolerance and px[2] > tolerance
        else px
        for px in pixels
    ]

    rgba_image.putdata(new_pixels)
    return rgba_image


def crop_center(pil_image, crop_width, crop_height):
    """
    Découpe une image en conservant uniquement la zone centrale.

    Objectif :
    - Transformer des photos hétérogènes en images carrées
    - Préserver le sujet principal (souvent centré)

    :param pil_image: Image PIL
    :param crop_width: largeur de découpe
    :param crop_height: hauteur de découpe
    :return: Image PIL découpée
    """
    img_width, img_height = pil_image.size

    return pil_image.crop((
        (img_width - crop_width) // 2,
        (img_height - crop_height) // 2,
        (img_width + crop_width) // 2,
        (img_height + crop_height) // 2
    ))

# ============================================================
# FONCTION DE VALIDATION DE PLACEMENT D'UNE PHOTO
# ============================================================


def check_placement(
    canvas_array,
    mask_alpha,
    x_coord,
    y_coord,
    photo_size,
    allowed_overlap_px
):
    """
    Vérifie si une photo peut être placée à une position donnée.

    Conditions :
    1. La photo doit être entièrement dans le masque
    2. La majorité de la zone doit être opaque (masque alpha)
    3. Le chevauchement avec les photos existantes est limité

    :return: True si le placement est valide, False sinon
    """

    # Sort du canvas
    if (
        y_coord + photo_size >= mask_alpha.shape[0]
        or x_coord + photo_size >= mask_alpha.shape[1]
    ):
        return False

    # Zone du masque insuffisamment opaque
    if np.count_nonzero(
        mask_alpha[
            y_coord:y_coord + photo_size,
            x_coord:x_coord + photo_size
        ]
    ) < (photo_size ** 2 * 0.9):
        return False

    # Trop de chevauchement avec des photos déjà placées
    if np.count_nonzero(
        canvas_array[
            y_coord:y_coord + photo_size,
            x_coord:x_coord + photo_size
        ]
    ) > allowed_overlap_px:
        return False

    return True

# ============================================================
# ESTIMATION DU TAUX DE REMPLISSAGE (SIMULATION)
# ============================================================


def estimate_fill_ratio(
    mask_alpha,
    photo_count,
    base_size,
    overlap_ration_percent,
    scale_list
):
    """
    Simule le placement des photos afin d'estimer :
    - le nombre de photos pouvant être placées
    - le taux de remplissage du masque

    Cette fonction NE MODIFIE PAS le rendu final,
    elle sert uniquement à proposer des réglages pertinents.

    :return: (nombre de photos placées, ratio de remplissage)
    """

    height, width = mask_alpha.shape
    sim_canvas = np.zeros_like(mask_alpha, dtype=np.uint8)

    remaining_photos = photo_count
    placed_photos = 0

    for scale_value in scale_list:
        sim_current_size = int(base_size * scale_value)

        # Taille trop petite, on ignore
        if sim_current_size < 15:
            continue

        sim_step = max(
            1,
            int(sim_current_size * (1 - overlap_ration_percent / 100))
        )

        max_allowed_overlap = int(
            sim_current_size ** 2 * (overlap_ration_percent / 100)
        )

        for y_coord in range(0, height - sim_current_size, sim_step):
            for x_coord in range(0, width - sim_current_size, sim_step):

                if remaining_photos <= 0:
                    break

                # Vérification masque
                if np.count_nonzero(
                    mask_alpha[
                        y_coord:y_coord + sim_current_size,
                        x_coord:x_coord + sim_current_size
                    ]
                ) < sim_current_size ** 2 * 0.9:
                    continue

                # Vérification chevauchement
                if np.count_nonzero(
                    sim_canvas[
                        y_coord:y_coord + sim_current_size,
                        x_coord:x_coord + sim_current_size
                    ]
                ) > max_allowed_overlap:
                    continue

                sim_canvas[
                    y_coord:y_coord + sim_current_size,
                    x_coord:x_coord + sim_current_size
                ] = 1

                placed_photos += 1
                remaining_photos -= 1

    fill_ratio = (
        np.count_nonzero(sim_canvas) /
        np.count_nonzero(mask_alpha)
    )

    return placed_photos, fill_ratio

# ============================================================
# INTERFACE UTILISATEUR STREAMLIT
# ============================================================


st.title("☁️ Générateur de Nuage de Collaborateurs")

st.header("1. Importation des fichiers")

col_up1, col_up2, col_up3 = st.columns(3)

with col_up1:
    mask_file = st.file_uploader(
        "Logo Client (Masque)",
        type=["png", "jpg", "jpeg"]
    )

with col_up2:
    photo_files = st.file_uploader(
        "Photos Collaborateurs",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

# ============================================================
# TRAITEMENT PRINCIPAL (LORSQUE LES FICHIERS SONT FOURNIS)
# ============================================================

if mask_file and photo_files:

    st.divider()
    st.header("2. Pré-traitement du masque")

    original_mask = Image.open(mask_file)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    with col_m2:
        st.markdown("##### Informations")
        st.success("Fond transparent détecté")
        st.info(f"Taille du mask : {original_mask.width} × {original_mask.height} px")

    with col_m4:
        st.markdown("##### Modifications éventuelles")
        new_width = st.number_input(
            "Largeur (px)",
            min_value=100,
            value=original_mask.width
        )
        new_height = st.number_input(
            "Hauteur (px)",
            min_value=100,
            value=original_mask.height
        )

    mask_image = original_mask.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS
    )

    # Gestion transparence selon le format
    if mask_image.mode != "RGBA":
        mask_image = (
            make_transparent(mask_image)
            if mask_file.type in ["image/jpeg", "image/jpg"]
            else mask_image.convert("RGBA")
        )

    with col_m1:
        st.image(mask_image, caption="Aperçu du masque", width=400)

    mask_alpha_array = np.array(mask_image)[:, :, 3]
    usable_pixels = np.count_nonzero(mask_alpha_array)

    # ========================================================
    # PRÉPARATION DES PHOTOS COLLABORATEURS
    # ========================================================

    processed_photos = []

    for photo_file in photo_files:
        photo_image = convert_to_rgba(Image.open(photo_file))
        side_size = min(photo_image.size)
        processed_photos.append(
            crop_center(photo_image, side_size, side_size)
        )

    st.divider()
    st.header("3. Configuration du nuage")

    st.markdown("##### 🏆 Top 5 des réglages (Objectif de remplissage > 75%)")

    scales = [1.0, 0.75, 0.55, 0.35]
    simulation_results = []

    # Simulation de plusieurs configurations
    for sim_photo_size in [70, 90, 110, 130, 150]:
        for sim_overlap in [15, 25, 35]:

            placed, fill = estimate_fill_ratio(
                mask_alpha_array,
                len(processed_photos),
                sim_photo_size,
                sim_overlap,
                scales
            )

            simulation_results.append({
                "Taille (px)": sim_photo_size,
                "Espace (%)": 0,
                "Chevauchement (%)": sim_overlap,
                "Photos Placées": placed,
                "Remplissage Est. (%)": round(min(98.0, fill * 100), 1)
            })

    df_top = (
        pd.DataFrame(simulation_results)
        .sort_values(by="Remplissage Est. (%)", ascending=False)
        .head(5)
    )

    st.table(df_top)
    best_config = df_top.iloc[0]

    # ========================================================
    # PARAMÈTRES UTILISATEUR
    # ========================================================

    col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)

    with col_p1:
        st.text("Taille photos (px)")
        chosen_size = st.number_input(
            "Taille photos (px)",
            value=int(best_config["Taille (px)"]),
            label_visibility="collapsed"
        )

    with col_p2:
        st.text("Espace (%)")
        spacing_percent = st.number_input(
            "Espace (%)",
            min_value=0,
            max_value=30,
            value=int(best_config["Espace (%)"]),
            label_visibility="collapsed"
        )

    with col_p3:
        st.text("Chevauchement (%)")
        overlap_percent = st.number_input(
            "Chevauchement (%)",
            min_value=0,
            max_value=50,
            value=int(best_config["Chevauchement (%)"]),
            label_visibility="collapsed"
        )

    with col_p5:
        st.text("Création du nuage")
        start_button = st.button(
            "Lancer la création 🚀",
            type="primary",
            width="stretch"
        )

    # ========================================================
    # GÉNÉRATION DU NUAGE FINAL
    # ========================================================

    if start_button:

        final_canvas = Image.new(
            "RGBA",
            mask_image.size,
            (0, 0, 0, 0)
        )

        canvas_array = np.zeros_like(mask_alpha_array)

        random.shuffle(processed_photos)
        photo_queue = processed_photos.copy()

        progress_bar = st.progress(0)
        status_text = st.empty()

        for scale_index, scale_factor in enumerate(scales):

            current_size = int(chosen_size * scale_factor)

            if current_size < 15:
                continue

            status_text.text(
                f"Passe {scale_index + 1}/{len(scales)} — Taille {current_size}px"
            )

            step = max(
                1,
                int(current_size * (1 + spacing_percent / 100 - overlap_percent / 100))
            )

            allowed_overlap = int(
                current_size ** 2 * (overlap_percent / 100)
            )

            for y_pos in range(0, new_height - current_size, step):
                for x_pos in range(0, new_width - current_size, step):

                    if not photo_queue:
                        break

                    if check_placement(
                        canvas_array,
                        mask_alpha_array,
                        x_pos,
                        y_pos,
                        current_size,
                        allowed_overlap
                    ):
                        photo = photo_queue.pop(0).resize(
                            (current_size, current_size),
                            Image.Resampling.LANCZOS
                        )

                        final_canvas.paste(photo, (x_pos, y_pos), photo)
                        canvas_array[
                            y_pos:y_pos + current_size,
                            x_pos:x_pos + current_size
                        ] = 255

            progress_bar.progress((scale_index + 1) / len(scales))

        status_text.text("Génération terminée !")

        st.divider()

    # ====================================================
    # AFFICHAGE NUAGE & STATISTIQUES & EXPORT
    # ====================================================

        col_res1, col_res2 = st.columns([3, 1])

        # Affichage nuage
        with col_res1:
            st.image(final_canvas, caption="Nuage généré", width='stretch')

        # Statistiques
        with col_res2:
            st.markdown("### Statistiques")

            placed_total = len(processed_photos) - len(photo_queue)
            st.metric("Photos placées", f"{placed_total}/{len(processed_photos)}")

            final_canvas_array = np.asarray(final_canvas)
            coverage = (np.count_nonzero(final_canvas_array[:, :, 3]) / usable_pixels) * 100
            st.metric("Remplissage Final", f"{coverage:.1f}%")

            if coverage >= 75:
                st.success("🎯 Objectif de 75% atteint !")
            else:
                st.warning(
                    "💡 Pour plus de remplissage, augmentez légèrement la résolution (largeur/hauteur) du masque."
                )

            # Export
            st.markdown("###")
            st.markdown("### Exports du nuage")

            buf_png, buf_pdf = io.BytesIO(), io.BytesIO()
            final_canvas.save(buf_png, format="PNG")
            final_canvas.convert("RGB").save(buf_pdf, format="PDF")

            st.download_button(
                "📥 Télécharger PNG",
                buf_png.getvalue(),
                "nuage.png",
                width='stretch')

            st.download_button(
                "📥 Télécharger PDF",
                buf_pdf.getvalue(),
                "nuage.pdf",
                width='stretch')
