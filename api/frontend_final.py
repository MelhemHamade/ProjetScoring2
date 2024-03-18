import streamlit as st
import requests

# Fonction pour récupérer les données du backend
def fetch_data(sk_id):
    response = requests.get(f'http://localhost:5000/api/data/{sk_id}')
    if response.status_code == 200:
        data = response.json()
        # séparer les données du client et les valeurs uniques
        client_data = {key: value for key, value in data.items() if key != 'unique_values'}
        unique_values = data['unique_values'] if 'unique_values' in data else {}
        return client_data, unique_values
    else:
        return None, {}

def unique_sorted_values_plus_ALL(array):
    unique = sorted(list(set(array)))  # Convertit en ensemble pour l'unicité, puis en liste pour trier
    unique.insert(0, "ALL")  # Ajoute "ALL" au début de la liste
    return unique

# Module pour afficher les données du client
def display_client_data(client_data, unique_values):
    st.write("Informations du client :")
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
        elif var == 'AGE':
            # Sélecteur d'âge
            age = st.slider('Âge', 18, 100, int(client_data[var]))
            client_data[var] = age
        elif var == 'CNT_CHILDREN':
            # Sélecteur pour le nombre d'enfants
            children_options = list(range(0, 11))  # Cela crée une liste de 0 à 10
            children = st.selectbox("Nombre d'enfants", options=children_options)

            client_data[var] = children
        else:
            # Fenêtres de saisie pour les autres variables
            val = st.number_input(f'{var} (actuel : {client_data[var]})', value=float(client_data[var]), step=0.01)
            client_data[var] = val

# Module pour générer l'analyse SHAP
def generate_shap_analysis(sk_id):
    # Construction de l'URL de l'API Flask pour envoyer la requête
    api_url = f"http://127.0.0.1:5000/generate_shap_plot?SK_ID_CURR={sk_id}"
    
    # Envoi de la requête GET à l'API Flask
    response = requests.get(api_url)
    
    # Traitement de la réponse
    if response.status_code == 200:
        data = response.json()
        
        # Récupération du chemin de l'image depuis la réponse JSON
        shap_plot_path = data.get('shap_plot_path')
        
        # Si un chemin d'image est fourni, construire l'URL complète de l'image
        if shap_plot_path:
            image_url = f"http://127.0.0.1:5000/static/images/{shap_plot_path}"
            # Affichage de l'image dans Streamlit
            st.image(image_url, caption='SHAP Plot')
        else:
            st.error("Le chemin de l'image SHAP Plot n'a pas été retourné par l'API.")
    else:
        # Affichage d'un message d'erreur si la requête à l'API échoue
        st.error("Erreur lors de la génération du SHAP Plot. Veuillez réessayer.")

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

# Module principal pour l'interface utilisateur
def main():
    st.title('Application combinée')

    # Section pour saisir l'ID du client
    sk_id = st.text_input('Entrez l\'ID du client :', '')

    # Affichage des données si un ID est saisi
    if sk_id:
        # Récupérer les données du backend
        client_data, unique_values = fetch_data(sk_id)
        if client_data:
            display_client_data(client_data, unique_values)

            # Bouton pour générer l'analyse SHAP
            if st.button('Générer l\'analyse SHAP'):
                generate_shap_analysis(sk_id)
        else:
            st.error('Erreur: Impossible de récupérer les données.')

if __name__ == '__main__':
    main()
