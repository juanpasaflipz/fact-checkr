/**
 * Stripe client-side utilities
 * Handles Stripe initialization and checkout session creation
 */

import { loadStripe, Stripe } from '@stripe/stripe-js';

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
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    // Get auth token from localStorage or cookies
    const token = localStorage.getItem('auth_token') || 
                  document.cookie.split('; ').find(row => row.startsWith('auth_token='))?.split('=')[1];
    
    const response = await fetch(`${apiUrl}/subscriptions/create-checkout-session`, {
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
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create checkout session');
    }
    
    const data = await response.json();
    return data.checkout_url;
  } catch (error) {
    console.error('Error creating checkout session:', error);
    return null;
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
  const checkoutUrl = await createCheckoutSession(tier, billingCycle, trialDays);
  
  if (checkoutUrl) {
    window.location.href = checkoutUrl;
  } else {
    throw new Error('Failed to create checkout session');
  }
};

