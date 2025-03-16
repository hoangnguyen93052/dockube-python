import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import sys
import json

class RecommendationSystem:
    def __init__(self, data):
        self.data = data
        self.user_item_matrix = None
        self.model = None
        self.scaler = StandardScaler()
        self.similarity_matrix = None

    def preprocess_data(self):
        print("Preprocessing data...")
        self.user_item_matrix = self.data.pivot(index='user_id', columns='item_id', values='rating').fillna(0)
        self.user_item_matrix = self.scaler.fit_transform(self.user_item_matrix)

    def compute_cosine_similarity(self):
        print("Computing cosine similarity...")
        self.similarity_matrix = cosine_similarity(self.user_item_matrix)

    def fit(self):
        self.preprocess_data()
        self.compute_cosine_similarity()
        self.model = NearestNeighbors(metric='cosine')
        self.model.fit(self.user_item_matrix)

    def get_recommendations(self, user_id, num_recommendations=5):
        user_index = self.data[self.data.user_id == user_id].index[0]
        distances, indices = self.model.kneighbors(self.user_item_matrix[user_index].reshape(1, -1), n_neighbors=num_recommendations + 1)
        similar_users_indices = indices.squeeze()[1:]  # Skip the first index as it's the user themselves
        recommended_items = []

        for i in similar_users_indices:
            recommended_items.extend(self.data.iloc[i]['item_id'].values)
        
        recommended_items = list(set(recommended_items))  # Unique items
        print(f"Recommendations for user {user_id}: {recommended_items[:num_recommendations]}")
        return recommended_items[:num_recommendations]

def load_data(file_path):
    print("Loading data...")
    return pd.read_csv(file_path)

def main():
    if len(sys.argv) != 2:
        print("Usage: python ai_recommendation_system.py <data_file>")
        sys.exit(1)

    data_file = sys.argv[1]
    
    try:
        data = load_data(data_file)
        # Ensure the data contains the necessary columns
        if not all(col in data.columns for col in ['user_id', 'item_id', 'rating']):
            raise ValueError("Input data must contain 'user_id', 'item_id', and 'rating' columns.")
        
        recommender = RecommendationSystem(data)
        recommender.fit()
        
        user_id = int(input("Enter user ID for recommendations: "))
        recommender.get_recommendations(user_id)

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()