from __future__ import annotations

import stripe


def create_checkout_session(
    *,
    api_key: str,
    price_id: str,
    success_url: str,
    cancel_url: str,
    telegram_user_id: str,
    purchase_type: str,
    credits_purchased: int,
    customer_id: str | None = None,
) -> stripe.checkout.Session:
    stripe.api_key = api_key

    params: dict[str, object] = {
        "mode": "payment",
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "client_reference_id": telegram_user_id,
        "metadata": {
            "telegram_user_id": telegram_user_id,
            "purchase_type": purchase_type,
            "credits_purchased": str(credits_purchased),
        },
    }

    if customer_id:
        params["customer"] = customer_id
    else:
        params["customer_creation"] = "always"

    return stripe.checkout.Session.create(**params)
