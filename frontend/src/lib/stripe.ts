/**
 * Stripe client-side utilities
 * Handles Stripe initialization and checkout session creation
 */

import { loadStripe, Stripe } from '@stripe/stripe-js';
import { getApiBaseUrl } from './api-config';
import { auth } from './firebase';

let stripePromise: Promise<Stripe | null>;

/**
 * Initialize Stripe with publishable key
 * Returns a promise that resolves to the Stripe instance
 */
export const getStripe = (): Promise<Stripe | null> => {
  if (!stripePromise) {
    const publishableKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;

    if (!publishableKey) {
      console.warn('Stripe publishable key not found. Stripe features will be disabled.');
      return Promise.resolve(null);
    }

    stripePromise = loadStripe(publishableKey);
  }

  return stripePromise;
};

/**
 * Create a checkout session via backend API
 * @param tier - Subscription tier ('pro' or 'team')
 * @param billingCycle - Billing cycle ('month' or 'year')
 * @param trialDays - Optional trial period in days
 * @returns Checkout session URL or null if error
 */
export const createCheckoutSession = async (
  tier: 'pro' | 'team',
  billingCycle: 'month' | 'year',
  trialDays: number = 0
): Promise<string | null> => {
  try {
    const apiUrl = getApiBaseUrl();

    // Get auth token from Firebase
    let token = null;
    if (auth.currentUser) {
      token = await auth.currentUser.getIdToken();
    }

    // Construct URL properly - handle empty apiUrl case
    const endpoint = '/api/subscriptions/create-checkout-session';
    const url = apiUrl ? `${apiUrl}${endpoint}` : endpoint;

    console.log('Creating checkout session:', { url, tier, billingCycle, hasToken: !!token });

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
      },
      body: JSON.stringify({
        tier,
        billing_cycle: billingCycle,
        trial_days: trialDays,
      }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Redirect to signin if not authenticated
        window.location.href = '/signin?redirect=/subscription';
        throw new Error('Authentication required');
      }
      const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}: ${response.statusText}` }));
      throw new Error(error.detail || 'Failed to create checkout session');
    }

    const data = await response.json();
    return data.checkout_url;
  } catch (error: any) {
    // Enhanced error logging
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      const apiUrl = getApiBaseUrl();
      console.error('Network error - Failed to fetch checkout session:', {
        apiUrl,
        endpoint: '/api/subscriptions/create-checkout-session',
        fullUrl: apiUrl ? `${apiUrl}/api/subscriptions/create-checkout-session` : '/api/subscriptions/create-checkout-session',
        error: error.message,
        possibleCauses: [
          'Backend server is not running or not accessible',
          'CORS configuration issue',
          'Network connectivity problem',
          'SSL/certificate issue'
        ]
      });
      throw new Error('No se pudo conectar con el servidor. Por favor, verifica tu conexión a internet e intenta de nuevo.');
    }
    console.error('Error creating checkout session:', error);
    throw error; // Re-throw to let caller handle it
  }
};

/**
 * Redirect to Stripe checkout
 * @param tier - Subscription tier
 * @param billingCycle - Billing cycle
 * @param trialDays - Optional trial period
 */
export const redirectToCheckout = async (
  tier: 'pro' | 'team',
  billingCycle: 'month' | 'year',
  trialDays: number = 0
): Promise<void> => {
  try {
    const checkoutUrl = await createCheckoutSession(tier, billingCycle, trialDays);

    if (checkoutUrl) {
      window.location.href = checkoutUrl;
    } else {
      throw new Error('No se pudo crear la sesión de pago. Por favor, intenta de nuevo.');
    }
  } catch (error) {
    // Re-throw with user-friendly message
    const message = error instanceof Error ? error.message : 'Error desconocido al crear la sesión de pago';
    throw new Error(message);
  }
};
