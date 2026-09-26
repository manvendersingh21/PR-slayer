
@app.post("/refunds")
def create_refund(refund: Refund):
    """Create a refund for a payment"""
    if refund.payment_id not in payments_db:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment = payments_db[refund.payment_id]
    
    # BUG: Missing authorization check! Should verify user owns the order
    
    refund_id = str(uuid.uuid4())
    refund_data = {
        "id": refund_id,
        "payment_id": refund.payment_id,
        "amount": refund.amount,
        "status": "completed",
        "created_at": datetime.utcnow().isoformat()
    }
    
    return refund_data


class Refund(BaseModel):
    payment_id: str
    amount: float
    user_id: str
