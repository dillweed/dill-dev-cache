def calculate_orders(current_price, target_price, total_amount, num_orders, scale):
    try:
        current_price = float(current_price)
        target_price = float(target_price)
        total_amount = float(total_amount)
        num_orders = int(num_orders)
        scale = float(scale)
        mult = 1.0
        order_mult = [1.0]
        for n in range(int(num_orders) - 1):
            mult *= scale
            order_mult.append(float(mult))

        divisor = sum(order_mult)
        order_unit = total_amount / divisor
        order_amounts = [round(x * order_unit, 2) for x in order_mult]

        difference = target_price - current_price
        diff_step = difference / num_orders
        limit_prices = [current_price + n * diff_step for n in range(1, int(num_orders) + 1)]

        return [{'amount': amt, 'price': price} for amt, price in zip(order_amounts, limit_prices)]
    except Exception as e:
        print(f'Error in calculate_orders: {e}')
        raise
