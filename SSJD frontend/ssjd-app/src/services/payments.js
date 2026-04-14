import api from './api';

export const paymentsService = {
  createOrder: (purpose, entityId, amount) =>
    api.post('/payments/create-order', null, { params: { purpose, entity_id: entityId, amount } }).then(r => r.data),

  verifyPayment: (razorpayOrderId, razorpayPaymentId, razorpaySignature) =>
    api.post('/payments/verify', null, {
      params: { razorpay_order_id: razorpayOrderId, razorpay_payment_id: razorpayPaymentId, razorpay_signature: razorpaySignature },
    }).then(r => r.data),

  list: (params) => api.get('/payments/', { params }).then(r => r.data),
};
