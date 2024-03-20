#!/usr/bin/env python
# coding: utf-8

# # SECTION 1: IMPORTATION DES MODULES

# In[4]:


# Modules nécessaires pour le traitement des données, la visualisation, et le déploiement de l'application web.
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Utilise le backend 'Agg' pour le rendu des graphiques sans interface graphique.
import shap
import joblib
from joblib import load
import pickle
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import pandas as pd
import os
import numpy as np
import pandas as pd
import seaborn as sns
# Ajout du chemin du dossier src pour l'importation des modules personnalisés.
sys.path.insert(0, '../src')
from TestCleaning import TestCleaningPipeline


# # SECTION 2: DÉFINITION DE LA CLASSE POUR L'ANALYSE SHAP

# In[2]:


class SHAPAnalysis:
    """Classe pour réaliser l'analyse SHAP sur un modèle."""
    
    def __init__(self, custom_model):
        """Initialisation avec un modèle personnalisé."""
        self.custom_model = custom_model
        self.explainer = shap.TreeExplainer(custom_model.model)

    def fit(self, X, y=None):
        """Fit n'est pas nécessaire ici, mais est inclus pour compatibilité."""
        return self

    def plot_shap_bar(self, single_observation_df, sk_id_curr, drop_columns=None, shap_threshold=0.1):
        if 'SK_ID_CURR' in single_observation_df.columns:
            single_observation_df = single_observation_df.drop(columns=['SK_ID_CURR'])
    
        predicted_proba = self.custom_model.model.predict_proba(single_observation_df)
        predicted_class = (predicted_proba[:, 1] >= self.custom_model.threshold).astype(int)
    
        shap_values = self.explainer.shap_values(single_observation_df)
        if isinstance(shap_values, list):
            shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        shap_values = shap_values.flatten()
    
        shap_abs = np.abs(shap_values)
        shap_mask = shap_abs > shap_threshold
        shap_df = pd.DataFrame(shap_values[shap_mask], index=single_observation_df.columns[shap_mask], columns=['SHAP Value'])
    
        null_cols_to_drop = [col for col in single_observation_df.columns if col in shap_df.index and single_observation_df[col].values[0] == 0]
        shap_df = shap_df.drop(null_cols_to_drop, axis=0)
    
        nan_cols_to_drop = [col for col in shap_df.index if col.endswith('_nan')]
        shap_df = shap_df.drop(nan_cols_to_drop)
    
        if not shap_df.empty:
            shap_df = shap_df.sort_values(by='SHAP Value', ascending=False)
    
            fig, ax = plt.subplots(figsize=(16, 9))
            colors = ['green' if val < 0 else 'red' for val in shap_df['SHAP Value']]
            bars = shap_df['SHAP Value'].plot(kind='barh', color=colors, ax=ax)
            ax.axvline(x=0, color='black', linestyle='--')
    
            for bar, col_name, value in zip(bars.patches, shap_df.index, shap_df['SHAP Value']):
                if value < 0:
                    text_color = 'green'
                else:
                    text_color = 'red'
                bar_width = bar.get_width()
                bar_height = bar.get_height()
                ax.text(bar_width / 2, bar.get_y() + bar_height / 2, f'{int(value)}', 
                        ha='center', va='center', color=text_color)
    
            decision_info = f'Décision de la demande de prêt : {"Refusée" if predicted_class[0] == 1 else "Acceptée"}'
            proba_info = f'Probabilité de non-remboursement : {predicted_proba[0][1]:.2f}'
            threshold_info = f'Seuil de décision : {self.custom_model.threshold:.2f}'
    
            ax.text(0.5, 1.1, f'{decision_info}\n{proba_info}\n{threshold_info}', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, bbox=dict(facecolor='none', edgecolor='black', boxstyle='round,pad=1'))
    
            # Justification de la décision sous forme de ligne horizontale
            threshold_x = self.custom_model.threshold * 100  # Conversion en pourcentage
            proba_x = predicted_proba[0][1] * 100  # Probabilité de défaut en pourcentage
    
    
            ax.set_yticks(range(-2, len(shap_df) + 2))
            ax.set_yticklabels(['', '', *shap_df.index, '', ''])
            ax.set_ylim(-3, len(shap_df.index))
    
            ax.set_xlabel('Impact sur la décision')
    
            plt.subplots_adjust(left=0.3)
    
            image_directory = os.path.join(app.root_path, 'static', 'images')
            os.makedirs(image_directory, exist_ok=True)
            image_path = os.path.join(image_directory, f'shap_plot_SK_ID_CURR_{sk_id_curr}.png')
            plt.savefig(image_path)
            plt.close(fig)
    
            relative_image_path = f'shap_plot_SK_ID_CURR_{sk_id_curr}.png'
    
            return relative_image_path
        else:
            print("Aucune caractéristique avec une importance non nulle pour cette observation.")
            return None

 

# # SECTION 3: CHARGEMENT DU MODÈLE ET CONFIGURATION

# In[7]:


# Chargement du modèle préentraîné et de son seuil optimal.
loaded_model_info = joblib.load('./models/model_and_threshold.joblib')
loaded_model, loaded_optimal_threshold = loaded_model_info

# Classe pour accueillir le modèle
class CustomThresholdModel:
    def __init__(self, model, threshold=0.5):
        self.model = model
        self.threshold = threshold

    def predict(self, X):
        # Utiliser predict_proba pour obtenir les probabilités
        probabilities = self.model.predict_proba(X)
        
        # Appliquer le seuil personnalisé pour déterminer les classes
        return (probabilities[:, 1] >= self.threshold).astype(int)

# Modèle avec optimal threshold
custom_model = CustomThresholdModel(model=loaded_model, threshold=loaded_optimal_threshold)

# Charger les données brutes fusionnées
test_merged = pd.read_csv('../data/test_merged.csv')


# Charger les données configuration du pipeline d'alignement à partir du fichier pickle
with open('../data/utils_data.pkl', 'rb') as file:
    loaded_data = pickle.load(file)

# Accéder aux données individuelles à partir du dictionnaire chargé
non_binary_vars = loaded_data['non_binary_vars']
large_continuous_variables = loaded_data['large_continuous_variables']
normalization_stats = loaded_data['normalization_stats']
stats_train = loaded_data['stats_df']
train_numeric_columns_excluding_target = loaded_data['num_cols_without_target']
train_filtered_columns_excluding_target = loaded_data['columns_without_target']

# Configuration du pipeline global
align_test_pipeline = TestCleaningPipeline(
    large_continuous_variables=large_continuous_variables,
    non_binary_vars=non_binary_vars,
    normalization_stats=normalization_stats,
    num_std=3,
    small_value=1e-6,
    stats_train=stats_train,
    train_numeric_columns=train_numeric_columns_excluding_target,
    train_filtered_columns=train_filtered_columns_excluding_target)


# Fonction pour réordonner les colonnes du dataframe en fonction des features du modèle.
def reorder_dataframe_columns(dataframe, model, id_column='SK_ID_CURR'):
    # Extraction des noms des features du modèle
    if hasattr(model, 'feature_names_in_'):
        model_features = list(model.feature_names_in_)  # Assurez-vous que c'est une liste
    elif hasattr(model, 'get_booster'):
        model_features = model.get_booster().feature_names
        if not isinstance(model_features, list):
            model_features = list(model_features)  # Convertir en liste si nécessaire
    else:
        raise ValueError("Impossible de déterminer les features du modèle.")
    
    # Vérifier si toutes les features du modèle sont dans le dataframe
    missing_features = set(model_features) - set(dataframe.columns)
    extra_features = set(dataframe.columns) - set(model_features) - {id_column}

    if missing_features:
        raise ValueError(f"Les features suivantes sont manquantes dans le dataframe: {missing_features}")
    if extra_features - {id_column}:
        raise ValueError(f"Le dataframe contient des features supplémentaires non présentes dans le modèle: {extra_features - {id_column}}")

    # Vérifier si la colonne d'identifiant est déjà une feature du modèle
    if id_column in model_features:
        ordered_columns = model_features  # La colonne d'identifiant est déjà incluse dans les features du modèle
    else:
        ordered_columns = [id_column] + model_features  # Ajouter la colonne d'identifiant uniquement si elle n'est pas incluse dans les features du modèle

    reordered_dataframe = dataframe[ordered_columns].copy()
    
    return reordered_dataframe


def bivariate_analysis(selected_variables, data):
    # Vérifier que les variables sélectionnées sont valides
    if len(selected_variables) == 2:
        # Créer une sous-trame avec les deux variables sélectionnées
        selected_data = data[selected_variables]
        
        # Générer l'analyse bivariée avec un seul graphique
        plt.figure(figsize=(8, 6))
        sns.scatterplot(data=selected_data, x=selected_variables[0], y=selected_variables[1])
        plt.xlabel(selected_variables[0])
        plt.ylabel(selected_variables[1])
        plt.title('Analyse Bivariée')
        
        # Enregistrer le graphique dans un fichier
        image_directory = os.path.join(app.root_path, 'static', 'images')
        os.makedirs(image_directory, exist_ok=True)
        image_path = os.path.join(image_directory, 'bivariate_analysis.png')
        plt.savefig(image_path)
        
        # Fermer la figure
        plt.close()
        
        return image_path
    else:
        return None


# Initialisation de l'application Flask
app = Flask(__name__)

# Activation des Cross-Origin Resource Sharing (CORS) pour l'application Flask
CORS(app)

# Chemin vers le dossier de données et modèle (adaptez selon structure de fichiers)
data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'test_merged.csv')

# Charger les données depuis le fichier CSV une seule fois au démarrage de l'application
data = pd.read_csv(data_path)


@app.route('/')
def index():
    # Route principale qui retourne la page HTML pour l'interface utilisateur
    return render_template('index.html')

@app.route('/api/data/<int:sk_id>', methods=['GET'])
def get_data(sk_id):

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

    # Sélectionner l'observation selon son id
    client_data = data[data['SK_ID_CURR'] == sk_id].to_dict(orient='records')
    unique_values = {}
    
    # Pour chaque variable catégorielle, obtenez les valeurs uniques dans la colonne
    categorical_variables = ['NAME_CONTRACT_TYPE', 'NAME_FAMILY_STATUS', 'NAME_HOUSING_TYPE','FLAG_MOBIL',
    'FLAG_EMAIL']
    for var in categorical_variables:
        unique_values[var] = data[var].unique().tolist()

    # Récupérer les valeurs extrêmes et la moyenne des variables numériques
    extreme_values = {}
    numerical_variables = ['AMT_INCOME_TOTAL', 'AMT_CREDIT', 'AMT_ANNUITY', 'AMT_GOODS_PRICE']
    for var in numerical_variables:
        extreme_values[var] = {
            'min': np.min(data[var]),
            'max': np.max(data[var]),
            'mean': np.mean(data[var])
        }
        
        # Vérifier s'il y a des valeurs extrêmes trouvées
        if np.isnan(extreme_values[var]['min']) or np.isnan(extreme_values[var]['max']):
            print(f"Aucune valeur extrême trouvée pour la variable {var}")

    if client_data:
        # Sélectionner uniquement les variables nécessaires
        selected_data = {var: client_data[0][var] for var in variables_to_display}
        # Ajouter les valeurs uniques pour les variables catégorielles
        selected_data['unique_values'] = unique_values
        # Ajouter les valeurs extrêmes pour les variables numériques
        selected_data['extreme_values'] = extreme_values
        return jsonify(selected_data)
    else:
        return jsonify({"error": "Client not found"}), 404


        
# Route pour générer le plot SHAP pour une observation spécifique via une requête GET.
@app.route('/generate_shap_plot', methods=['GET'])
def generate_shap_plot():
    
    
    # Récupération de l'identifiant SK_ID_CURR à partir des paramètres de la requête.
    sk_id_curr = request.args.get('SK_ID_CURR')
    
    # Vérification que le paramètre SK_ID_CURR a bien été fourni.
    if sk_id_curr is None:
        # Si le paramètre est manquant, renvoie une erreur 400 avec un message explicatif.
        return jsonify({"error": "Le paramètre SK_ID_CURR est manquant."}), 400

    try:
        # Tentative de conversion de l'identifiant en entier.
        sk_id_curr = int(sk_id_curr)
    except ValueError:
        # Si la conversion échoue, renvoie une erreur 400 indiquant que le paramètre doit être un entier valide.
        return jsonify({"error": "Le paramètre SK_ID_CURR doit être un entier valide."}), 400

    # Recherche des données du client correspondant à l'identifiant SK_ID_CURR dans le dataset préchargé.
    client_data = data[data['SK_ID_CURR'] == sk_id_curr]
    
    # Vérifie si des données pour le client spécifié ont été trouvées.
    if client_data.empty:
        # Si aucune donnée n'est trouvée, renvoie une erreur 404 avec un message approprié.
        return jsonify({"error": f"Aucun client trouvé avec SK_ID_CURR {sk_id_curr}."}), 404
    
    # Application des transformations nécessaires sur les données du client.
    client_data = align_test_pipeline.transform(client_data)
    # Réordonnancement des colonnes des données du client pour correspondre aux attentes du modèle.
    client_data = reorder_dataframe_columns(client_data, loaded_model, id_column='SK_ID_CURR')
    
    # Initialisation de l'analyse SHAP avec le modèle personnalisé.
    shap_analysis = SHAPAnalysis(custom_model)
    
    # Génération du plot SHAP pour les données du client et récupération du chemin du fichier image.
    shap_plot_path = shap_analysis.plot_shap_bar(client_data, sk_id_curr, drop_columns=['SK_ID_CURR'])
    
    # Vérification si le chemin du plot SHAP a été généré avec succès.
    if shap_plot_path is None:
        # Si la génération du graphique échoue, renvoie une erreur 500 avec un message d'erreur.
        return jsonify({"error": "Impossible de générer le graphique SHAP."}), 500

    # Si le graphique est généré avec succès, renvoie le chemin d'accès au fichier image du graphique.
    return jsonify({"shap_plot_path": shap_plot_path})


@app.route('/api/bivariate_analysis', methods=['POST'])
def calculate_bivariate_analysis():
    request_data = request.get_json()
    selected_variables = request_data['selected_variables']
    bivariate_plot_path = bivariate_analysis(selected_variables, data)
    print(f"le chemin bivariate_plot_path est : {bivariate_plot_path }")
    if bivariate_plot_path:
        # Retourner le chemin de l'image
        return jsonify({'bivariate_analysis_path': bivariate_plot_path})
    else:
        return jsonify({'error': 'Variables invalides'})

# La route Flask pour la mise à jour des données et la génération de l'analyse SHAP


@app.route('/api/update', methods=['POST'])
def update_data():
    # Recevoir les données du client depuis la requête POST
    updated_client_data = request.get_json()
    print(f"updated_client_data est : {updated_client_data}")
    
    # Vérification que les données reçues ne sont pas nulles
    if not updated_client_data:
        return jsonify({"error": "Aucune donnée reçue pour la mise à jour."}), 400

    # Convertir SK_ID_CURR en entier
    updated_client_data['SK_ID_CURR'] = int(updated_client_data['SK_ID_CURR'])

    # Convertir les données reçues en DataFrame
    client_data_df = pd.DataFrame.from_records([updated_client_data])

    # Afficher le DataFrame
    print(f"voilà le resultat client_data_df: {client_data_df.head()}")

    # Extraire l'identifiant du client
    sk_id_curr = updated_client_data['SK_ID_CURR']

    # Mettre à jour uniquement les colonnes existantes dans les données globales
    global data
    data.loc[data['SK_ID_CURR'] == sk_id_curr, client_data_df.columns] = client_data_df.values

    # Renvoyer la réponse
    return jsonify({"message": "Mise à jour réussie."})



if __name__ == '__main__':
    app.run(debug=True)

