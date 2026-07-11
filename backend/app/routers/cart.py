"""Cart endpoints — one shared demo cart (no auth/users in scope).

Adding the same product+size again merges into the existing line. Sizes are
validated against the product's size chart labels so the cart can't hold a
size the product doesn't come in.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import CartItem, Product
from app.schemas import CartItemIn, CartItemOut, CartResponse

router = APIRouter(prefix="/api/cart", tags=["cart"])


def _cart_response(db: Session) -> CartResponse:
    items = (
        db.query(CartItem).join(Product).order_by(CartItem.created_at, CartItem.id).all()
    )
    out = [
        CartItemOut(
            id=i.id, product_id=i.product_id, name=i.product.name,
            size=i.size, quantity=i.quantity, price=i.product.price,
        )
        for i in items
    ]
    return CartResponse(items=out, total=round(sum(i.price * i.quantity for i in out), 2))


@router.get("", response_model=CartResponse)
def get_cart(db: Session = Depends(get_db)) -> CartResponse:
    return _cart_response(db)


@router.post("/items", response_model=CartResponse)
def add_item(payload: CartItemIn, db: Session = Depends(get_db)) -> CartResponse:
    product = db.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    valid_sizes = {c.size_label for c in product.size_charts}
    if valid_sizes and payload.size not in valid_sizes:
        raise HTTPException(
            status_code=400,
            detail=f"Size '{payload.size}' not available; choose one of {sorted(valid_sizes)}",
        )

    line = (
        db.query(CartItem)
        .filter(CartItem.product_id == payload.product_id, CartItem.size == payload.size)
        .first()
    )
    if line:
        line.quantity += payload.quantity
    else:
        db.add(CartItem(product_id=payload.product_id, size=payload.size, quantity=payload.quantity))
    db.commit()
    return _cart_response(db)


@router.delete("/items/{item_id}", response_model=CartResponse)
def remove_item(item_id: int, db: Session = Depends(get_db)) -> CartResponse:
    line = db.get(CartItem, item_id)
    if line is None:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(line)
    db.commit()
    return _cart_response(db)
