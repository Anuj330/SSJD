import { useState } from 'react';
import { paymentsService } from '../services/payments';
import toast from 'react-hot-toast';

/**
 * Hook to handle Razorpay checkout flow.
 * Returns { pay, loading } where pay(purpose, entityId, amount, onSuccess) triggers the flow.
 */
export function useRazorpay() {
  const [loading, setLoading] = useState(false);

  const pay = async (purpose, entityId, amount, onSuccess) => {
    if (!window.Razorpay) {
      toast.error('Payment gateway not loaded. Please refresh the page.');
      return;
    }

    setLoading(true);
    try {
      const order = await paymentsService.createOrder(purpose, entityId, amount);

      const options = {
        key: order.razorpay_key_id,
        amount: order.amount_paise,
        currency: 'INR',
        name: 'SSJD Cooperative',
        description: `${purpose === 'deposit' ? 'Deposit' : 'Loan Repayment'} Payment`,
        order_id: order.razorpay_order_id,
        handler: async (response) => {
          try {
            const result = await paymentsService.verifyPayment(
              response.razorpay_order_id,
              response.razorpay_payment_id,
              response.razorpay_signature
            );
            toast.success(result.message || 'Payment successful!');
            onSuccess?.();
          } catch {
            toast.error('Payment verification failed. Contact admin if amount was debited.');
          }
        },
        theme: { color: '#4f46e5' },
      };

      const rzp = new window.Razorpay(options);
      rzp.on('payment.failed', (resp) => {
        toast.error(resp.error?.description || 'Payment failed');
      });
      rzp.open();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Could not initiate payment';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return { pay, loading };
}
