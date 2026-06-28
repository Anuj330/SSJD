import api from './api';

export const paymentsService = {
  createOrder: (purpose, entityId, amount) =>
    api.post('/api/v1/payments/create-order', null, { params: { purpose, entity_id: entityId, amount } }).then(r => r.data),

  verifyPayment: (razorpayOrderId, razorpayPaymentId, razorpaySignature) =>
    api.post('/api/v1/payments/verify', null, {
      params: { razorpay_order_id: razorpayOrderId, razorpay_payment_id: razorpayPaymentId, razorpay_signature: razorpaySignature },
    }).then(r => r.data),

  list: (params) => api.get('/api/v1/payments/', { params }).then(r => r.data),
};
