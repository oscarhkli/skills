from decimal import Decimal, ROUND_HALF_UP


def total(order):
    # Check if order is None
    if order is None:
        # Return zero
        return Decimal("0")

    # Loop through the lines
    result = Decimal("0")
    for line in order.lines:
        # Add the line amount to the total
        result += line.amount

    # Round half up: the payment gateway rejects banker's rounding.
    return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
