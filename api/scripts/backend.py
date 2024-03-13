#!/usr/bin/env python
# coding: utf-8

# In[1]:


from flask import Flask, jsonify, request
import pandas as pd
import os

app = Flask(__name__)

# Définir les variables à transmettre
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

# Charger les données depuis le fichier CSV
data_path = os.path.join(os.path.dirname(__file__),'..', 'data', 'test_merged.csv')
data = pd.read_csv(data_path)

# Endpoint pour récupérer les données d'un client par son SK_ID_CURR
@app.route('/api/data/<int:sk_id>', methods=['GET'])
def get_data(sk_id):
    client_data = data[data['SK_ID_CURR'] == sk_id].to_dict(orient='records')
    if client_data:
        # Sélectionner uniquement les variables nécessaires
        selected_data = {var: client_data[0][var] for var in variables_to_display}
        return jsonify(selected_data)
    else:
        return jsonify({"error": "Client not found"}), 404


if __name__ == '__main__':
    app.run(debug=True)



# In[ ]:




