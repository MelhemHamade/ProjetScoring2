import streamlit as st
import requests
import matplotlib.pyplot as plt
import io
from matplotlib.patches import Patch

def navbar():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Pages", ("Données du client", "Décision de la demande de prêt", "Comparaison de valeurs", "Analyse bivariée"))

    if page == "Données du client":
        st.title("Données du client")
        sk_id = st.text_input('Entrez l\'ID du client :', '')
        if sk_id:
            # Récupérer les données du client et les afficher
            client_data, unique_values, extreme_values = fetch_data(sk_id)
            if client_data:
                display_client_data(client_data, unique_values, extreme_values, sk_id)
            else:
                st.error('Erreur: Impossible de récupérer les données du client.')

    elif page == "Décision de la demande de prêt":
        st.title("Décision de la demande de prêt")
        sk_id = st.text_input('Entrez l\'ID du client :', '')
        if sk_id:
            # Générer et afficher l'analyse SHAP
            shap_data = generate_shap_analysis(sk_id)
            if shap_data is not None:
                st.error('Erreur: Impossible de générer l\'analyse SHAP.')
                st.error(shap_data)

    elif page == "Comparaison de valeurs":
        st.title("Comparaison de valeurs")
        sk_id = st.text_input('Entrez l\'ID du client :', '')
        if sk_id:
            # Récupérer les données du client
            client_data, _, extreme_values = fetch_data(sk_id)
            if client_data:
                # Afficher la comparaison de valeurs avec les extrêmes et la moyenne
                compare_to_stats(client_data, extreme_values)
            else:
                st.error('Erreur: Impossible de récupérer les données du client.')

    elif page == "Analyse bivariée":
        st.title("Analyse bivariée")
        sk_id = st.text_input('Entrez l\'ID du client :', '')
        if sk_id:
            # Récupérer les données du client
            client_data, _, _ = fetch_data(sk_id)
            if client_data:
                # Récupérer les noms de variables disponibles
                variables_to_display = list(client_data.keys())
                # Sélectionner les variables à comparer
                selected_variables = st.multiselect("Sélectionnez deux variables à comparer :", options=variables_to_display, default=[])
                if len(selected_variables) == 2:
                    # Afficher l'analyse bivariée avec les variables sélectionnées
                    bivariate_analysis(selected_variables)
                else:
                    st.error("Veuillez sélectionner exactement deux variables pour l'analyse bivariée.")
            else:
                st.error('Erreur: Impossible de récupérer les données du client.')

# Variables à afficher
variables_to_display = [
    'NAME_CONTRACT_TYPE',
    'AMT_INCOME_TOTAL',
    'AMT_CREDIT',
    'AMT_ANNUITY',
    'AMT_GOODS_PRICE',
    'CNT_CHILDREN',
    'NAME_FAMILY_STATUS',
    'NAME_HOUSING_TYPE',
    'AGE',
    'YEARS_EMPLOYED',
    'FLAG_MOBIL',
    'FLAG_EMAIL']


# Fonction pour récupérer les données du backend
def fetch_data(sk_id):
    response = requests.get(f'http://melhemhamade.pythonanywhere.com/api/data/{sk_id}')
    if response.status_code == 200:
        data = response.json()
        # Séparer les données du client et les valeurs uniques
        client_data = {key: value for key, value in data.items() if key != 'unique_values'}
        unique_values = data['unique_values'] if 'unique_values' in data else {}

        # Récupérer les valeurs extrêmes des variables numériques
        extreme_values = {}
        for var in ['AMT_INCOME_TOTAL', 'AMT_CREDIT', 'AMT_ANNUITY', 'AMT_GOODS_PRICE']:
            if var in data['extreme_values']:
                extreme_values[var] = data['extreme_values'][var]

        return client_data, unique_values, extreme_values
    else:
        return None, {}, {}

def unique_sorted_values_plus_ALL(array):
    unique = sorted(list(set(array)))  # Convertit en ensemble pour l'unicité, puis en liste pour trier
    unique.insert(0, "ALL")  # Ajoute "ALL" au début de la liste
    return unique


# Fonction pour afficher les données du client et permettre la modification
def display_client_data(client_data, unique_values, extreme_values, sk_id):
    # CSS pour augmenter le contraste et la visibilité des champs de saisie
    contrast_style = """
    <style>
    /* Augmentation du contraste pour les champs de saisie et select */
    .stTextInput input, .stSelectbox select, .stSlider .thumb, .stSlider .track {
        border: 2px solid #4f4f4f !important; /* Bordure plus visible */
        background-color: #ffffff !important; /* Fond blanc pour éviter la transparence */
    }
    
    /* Styles supplémentaires pour d'autres types de widgets si nécessaire */
    .stDateInput input, .stTimeInput input, .stNumberInput input, .stTextarea textarea {
        border: 2px solid #4f4f4f !important;
        background-color: #ffffff !important;
    }
    
    /* Amélioration du contraste pour le slider */
    .stSlider .slider-horizontal {
        background-color: #4f4f4f !important; /* Couleur de fond du slider */
    }
    .stSlider .slider-handle {
        border: 2px solid #4f4f4f !important; /* Bordure du handle du slider */
    }
    
    /* Styliser le bouton de soumission */
    .stButton > button {
        border: 2px solid #4f4f4f !important; /* Bordure du bouton */
        background-color: #4a86e8 !important; /* Couleur de fond bleue */
        color: white !important; /* Couleur du texte */
        font-size: 16px !important; /* Taille de la police */
        padding: 10px 24px !important; /* Padding intérieur */
        border-radius: 5px !important; /* Bordures arrondies */
    }
    
   
    .stButton > button:hover {
        background-color: #357abD !important; /* Couleur de fond plus foncée au survol */
    }
    
    .stButton > button:active {
        background-color: #22497c !important; /* Couleur de fond lors du clic */
    }
    </style>
    """
    
    st.markdown(contrast_style, unsafe_allow_html=True)
    

    st.write("### Informations du client :")
    
    # Déclarer le formulaire
    with st.form(key='client_data_form'):
        new_values = {}  # Variable pour stocker les nouvelles valeurs modifiées
        for var in variables_to_display:
            if var in unique_values:
                # Obtenir la liste des options uniques
                options = unique_sorted_values_plus_ALL(unique_values[var])

                # Définir la valeur actuelle comme valeur par défaut
                selected_option = st.selectbox(
                    label=f'{var}',
                    options=options,
                    index=options.index(client_data[var])  # La valeur actuelle est sélectionnée par défaut
                )
                # Vérifier si la valeur a été modifiée
                if selected_option != client_data[var]:
                    new_values[var] = selected_option  # Stocker la nouvelle valeur modifiée
                client_data[var] = selected_option  # Mettre à jour les données du client
            elif var == 'AGE':
                # Sélecteur d'âge
                age = st.slider('Âge', 18, 100, client_data[var])
                if age != client_data[var]:
                    new_values[var] = age
                client_data[var] = age  # Mettre à jour les données du client
            elif var == 'CNT_CHILDREN':
                # Sélecteur pour le nombre d'enfants
                children_options = list(range(0, 11))  # Cela crée une liste de 0 à 10
                children = st.selectbox("Nombre d'enfants", options=children_options, index=client_data[var])
                if children != client_data[var]:
                    new_values[var] = children
                client_data[var] = children  # Mettre à jour les données du client
            else:
                # Fenêtres de saisie pour les autres variables
                val = st.number_input(f'{var} (actuel : {client_data[var]})', value=float(client_data[var]), step=0.01)
                if val != client_data[var]:
                    new_values[var] = val
                client_data[var] = val  # Mettre à jour les données du client

        # Ajouter le bouton de soumission du formulaire
        form_submit_button = st.form_submit_button(label='Mettre à jour')
    
    # Lors de la soumission du formulaire, envoyer uniquement les valeurs modifiées au backend
    if form_submit_button:
        send_new_values(new_values, sk_id)
        st.write("Données mises à jour avec succès!")

    # Retourner les données du client mises à jour
    return client_data
                    
# Fonction pour envoyer les nouvelles valeurs au backend
def send_new_values(client_data, sk_id):
    client_data['SK_ID_CURR'] = sk_id  # Ajouter l'ID du client aux données
    response = requests.post('http://melhemhamade.pythonanywhere.com/api/update', json=client_data)
    if response.status_code != 200:
        st.error("Une erreur s'est produite lors de la mise à jour des valeurs.")

# Module pour générer l'analyse SHAP
def generate_shap_analysis(sk_id):
    # Construction de l'URL de l'API Flask pour envoyer la requête
    api_url = f"http://melhemhamade.pythonanywhere.com/generate_shap_plot?SK_ID_CURR={sk_id}"
    
    # Envoi de la requête GET à l'API Flask
    response = requests.get(api_url)
    
    # Traitement de la réponse
    if response.status_code == 200:
        data = response.json()
        
        # Récupération du chemin de l'image depuis la réponse JSON
        shap_plot_path = data.get('shap_plot_path')
        
        # Si un chemin d'image est fourni, construire l'URL complète de l'image
        if shap_plot_path:
            image_url = f"http://melhemhamade.pythonanywhere.com/static/images/{shap_plot_path}"
            # Affichage de l'image dans Streamlit
            st.image(image_url, caption='SHAP Plot')
        else:
            return st.error("Le chemin de l'image SHAP Plot n'a pas été retourné par l'API.")
    else:
        # Affichage d'un message d'erreur si la requête à l'API échoue
        return st.error("Erreur lors de la génération du SHAP Plot. Veuillez réessayer.")

# Variables à afficher
variables_to_display = [
    'NAME_CONTRACT_TYPE',
    'AMT_INCOME_TOTAL',
    'AMT_CREDIT',
    'AMT_ANNUITY',
    'AMT_GOODS_PRICE',
    'CNT_CHILDREN',
    'NAME_FAMILY_STATUS',
    'NAME_HOUSING_TYPE',
    'AGE',
    'YEARS_EMPLOYED',
    'FLAG_MOBIL',
    'FLAG_EMAIL']


def compare_to_stats(client_data, extreme_values):
    st.subheader("Comparaison de la valeur avec les extrêmes et la moyenne :")
    selected_variable = st.selectbox("Sélectionnez une variable :", options=variables_to_display)
    
    if selected_variable in extreme_values:
        min_val = extreme_values[selected_variable].get('min', None)
        max_val = extreme_values[selected_variable].get('max', None)
        mean_val = extreme_values[selected_variable].get('mean', None)
        
        if min_val is not None and max_val is not None and mean_val is not None:
            client_value = client_data[selected_variable]
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot([min_val, max_val], [0, 0], color='black')  # Ligne entre les extrêmes
            ax.scatter([min_val, max_val, mean_val, client_value], [0, 0, 0, 0], color=['red', 'red', 'green', 'blue'], s=100) # Augmentez la taille des marqueurs
            ax.set_xlabel(selected_variable)
            ax.set_yticks([])
            
            # Créer des objets Patch pour la légende personnalisée
            legend_handles = [
                Patch(color='red', label=f'Min: {min_val}'),
                Patch(color='green', label=f'Mean: {mean_val}'),
                Patch(color='blue', label=f'Current: {client_value}'),
                Patch(color='red', label=f'Max: {max_val}')
            ]
            ax.legend(handles=legend_handles, loc='center', bbox_to_anchor=(0.5, -0.2), ncol=4) # Réglage de la position de la légende
            st.pyplot(fig)
        else:
            st.error("Les statistiques de comparaison ne sont pas disponibles pour cette variable.")
    else:
        st.error("Les statistiques de comparaison ne sont pas disponibles pour cette variable.")


def bivariate_analysis(selected_variables):
    # Envoyer uniquement les deux variables sélectionnées au backend
    response = requests.post('http://melhemhamade.pythonanywhere.com/api/bivariate_analysis', json={'selected_variables': selected_variables})
    if response.status_code == 200:
        # Récupérer le chemin de l'image de la réponse JSON
        bivariate_plot_path = response.json().get('bivariate_analysis_path')
        if bivariate_plot_path:
            # URL complète de l'image
            image_url = "https://melhemhamade.pythonanywhere.com/static/images/bivariate_analysis.png"
            # Afficher l'image dans Streamlit
            st.image(image_url, caption='Analyse Bivariée')
        else:
            st.error("Erreur: Impossible de récupérer l'analyse bivariée.")
    else:
        st.error("Erreur: Impossible de contacter le serveur.")



# Point d'entrée principal de l'application Streamlit
# App principale
def main():
    st.set_page_config(page_title="Application de décision de prêt", page_icon=":chart_with_upwards_trend:")
    navbar()

if __name__ == "__main__":
    main()

