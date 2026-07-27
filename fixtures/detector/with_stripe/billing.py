import stripe

charge = stripe.Charge.create(source="tok_123")
