import streamlit as st
import requests
import matplotlib.pyplot as plt



# Barre de navigation
def navbar():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Pages", ("Données du client", "Décision de la demande de prêt"))

    if page == "Données du client":
        st.title("Données du client")
        sk_id = st.text_input('Entrez l\'ID du client :', '')
        if sk_id:
            # Récupérer les données du client et les afficher
            client_data, unique_values, extreme_values = fetch_data(sk_id)
            if client_data:
                display_client_data(client_data, unique_values, extreme_values)
            else:
                st.error('Erreur: Impossible de récupérer les données du client.')

            # Appel de la fonction dashboard
            dashboard(sk_id)

    elif page == "Décision de la demande de prêt":
        st.title("Décision de la demande de prêt")
        sk_id = st.text_input('Entrez l\'ID du client :', '')
        if sk_id:
            # Générer et afficher l'analyse SHAP
            shap_data = generate_shap_analysis(sk_id)
            if shap_data:
                display_shap_analysis(shap_data)
            else:
                st.error('Erreur: Impossible de générer l\'analyse SHAP.')


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
    response = requests.get(f'http://localhost:5000/api/data/{sk_id}')
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


# Fonction pour afficher les données du client
def display_client_data(client_data, unique_values, extreme_values):
    st.write("Informations du client :")
    
    # Déclarer le formulaire
    with st.form(key='client_data_form'):
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
                client_data[var] = selected_option  # Mettre à jour les données du client
            elif var == 'AGE':
                # Sélecteur d'âge
                age = st.slider('Âge', 18, 100, client_data[var])
                client_data[var] = age  # Mettre à jour les données du client
            elif var == 'CNT_CHILDREN':
                # Sélecteur pour le nombre d'enfants
                children_options = list(range(0, 11))  # Cela crée une liste de 0 à 10
                children = st.selectbox("Nombre d'enfants", options=children_options, index=client_data[var])
                client_data[var] = children  # Mettre à jour les données du client
            else:
                # Fenêtres de saisie pour les autres variables
                val = st.number_input(f'{var} (actuel : {client_data[var]})', value=float(client_data[var]), step=0.01)
                client_data[var] = val  # Mettre à jour les données du client

                # Afficher la ligne entre les extrêmes avec la moyenne et la valeur actuelle
                if var in extreme_values:
                    min_val = extreme_values[var].get('min', None)
                    max_val = extreme_values[var].get('max', None)
                    mean_val = extreme_values[var].get('mean', None)
                    if min_val is not None and max_val is not None and mean_val is not None:
                        plt.figure(figsize=(8, 2))
                        plt.plot([min_val, max_val], [0, 0], color='black')  # Ligne entre les extrêmes
                        plt.scatter([min_val, max_val, mean_val, client_data[var]], [0, 0, 0, 0], color=['red', 'red', 'green', 'blue'], label=['Min', 'Max', 'Mean', 'Current'])
                        plt.xlabel(var)
                        plt.yticks([])
                        plt.legend()
                        st.pyplot(plt)
                        
        # Ajouter le bouton de soumission du formulaire
        form_submit_button = st.form_submit_button(label='Mettre à jour')

    # Retourner les données du client mises à jour
    return client_data, form_submit_button

    # Bouton pour envoyer les nouvelles valeurs au backend
    #if st.button('Mettre à jour les valeurs'):
        #send_new_values(client_data)
                    
# Fonction pour envoyer les nouvelles valeurs au backend
def send_new_values(client_data):
    response = requests.post('http://localhost:5000/api/update', json=client_data)
    if response.status_code == 200:
        st.success("Les nouvelles valeurs ont été mises à jour avec succès!")
    else:
        st.error("Une erreur s'est produite lors de la mise à jour des valeurs.")

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

def dashboard(sk_id):
    # Récupérer les données du backend
    client_data, unique_values, extreme_values = fetch_data(sk_id)
    if client_data:
        # Bouton pour générer l'analyse SHAP
        if st.button('Générer l\'analyse SHAP'):
            generate_shap_analysis(sk_id)
        # Bouton pour afficher les données
        if st.button('Afficher les données du client'):
            display_client_data(client_data, unique_values, extreme_values)
    else:
        st.error('Erreur: Impossible de récupérer les données.') 
    

# Point d'entrée principal de l'application Streamlit
# App principale
def main():
    st.set_page_config(page_title="Application de décision de prêt", page_icon=":chart_with_upwards_trend:")
    navbar()

if __name__ == "__main__":
    main()

