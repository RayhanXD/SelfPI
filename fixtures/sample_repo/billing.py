import stripe

# True call site — must be found (recall = 100% on fixtures)
charge = stripe.Charge.create(source="tok_123")

# False positive trap — in a comment, should not score as a real site
# stripe.Charge.create(source="tok_comment")

def refund():
    return stripe.Charge.create(source=customer_card)
