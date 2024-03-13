#!/usr/bin/env python
# coding: utf-8

# In[4]:


import streamlit as st
import pandas as pd
import requests

# Définir les variables à afficher
variables_to_display = [
    'SK_ID_CURR',
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
        return data
    else:
        return None

# Fonction principale pour l'interface utilisateur
def main():
    st.title('Affichage des données')

    # Saisie de l'ID
    sk_id = st.text_input('Entrez l\'ID du client :')

    # Affichage des données si un ID est saisi
    if sk_id:
        # Récupérer les données du backend
        data = fetch_data(sk_id)
        if data:
            # Afficher les variables sélectionnées
            selected_data = {var: data[var] for var in variables_to_display}
            st.write(selected_data)
        else:
            st.error('Erreur: Impossible de récupérer les données.')

if __name__ == '__main__':
    main()



# In[ ]:




