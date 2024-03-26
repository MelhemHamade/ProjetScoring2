#!/usr/bin/env python
# coding: utf-8

# In[4]:


import streamlit as st
import pandas as pd
import requests

# Définir les variables à afficher
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



# Fonction principale pour l'interface utilisateur
def main():
    st.title('Affichage des données')

    # Saisie de l'ID
    sk_id = st.text_input('Entrez l\'ID du client :', '')

    # Affichage des données si un ID est saisi
    if sk_id:
        # Récupérer les données du backend
        client_data, unique_values = fetch_data(sk_id)
        if client_data:
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
        else:
            st.error('Erreur: Impossible de récupérer les données.')

if __name__ == '__main__':
    main()



# In[ ]:




