import firebase_admin
from firebase_admin import credentials, firestore
import os
import streamlit as st

def initialize_firebase():
    """
    Initialize Firebase Admin SDK.
    
    Strategy:
    1. Try to use specific serviceAccountKey.json if it exists (Local development).
    2. Fallback to Application Default Credentials (ADC) (Cloud Run deployment).
    """
    try:
        # Check if app is already initialized
        if not firebase_admin._apps:
            key_path = "serviceAccountKey.json"
            
            if os.path.exists(key_path):
                # Local development with explicit key
                cred = credentials.Certificate(key_path)
                firebase_admin.initialize_app(cred)
                print("Firebase initialized with serviceAccountKey.json")
            else:
                # Cloud Run / Production (uses Google Cloud default credentials)
                firebase_admin.initialize_app()
                print("Firebase initialized with Application Default Credentials")
                
        return firestore.client()
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        return None
