// Import the functions you need from the SDKs you need
import { initializeApp, getApps } from "firebase/app";
import { getAuth } from "firebase/auth";

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

// Debug config
if (typeof window !== 'undefined') {
    console.log('[Firebase Init] Config:', {
        authDomain: firebaseConfig.authDomain,
        projectId: firebaseConfig.projectId,
        hasApiKey: !!firebaseConfig.apiKey,
        apiKeyPrefix: firebaseConfig.apiKey ? firebaseConfig.apiKey.substring(0, 5) + '...' : 'N/A'
    });
}

// Initialize Firebase
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
const auth = getAuth(app);

export { app, auth };
