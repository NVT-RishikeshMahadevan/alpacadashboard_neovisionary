import streamlit as st
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType, QueryOrderStatus
import pandas as pd
from datetime import datetime, timedelta

# Initialize session state for messages
if 'message' not in st.session_state:
    st.session_state.message = None

def create_trading_client():
    api_key = "PK25YZNBYBYX0XQJNK5A"
    secret_key = "CfZx1CtNITOdYKpwxVYCec02k6WBT0EJBYSS5WgZ"
    return TradingClient(api_key=api_key, secret_key=secret_key, paper=True)

def place_market_order(symbol, qty, side):
    client = create_trading_client()
    try:
        # Convert symbol to uppercase
        symbol = symbol.upper()
        order_request = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.GTC,
            type=OrderType.MARKET
        )
        order = client.submit_order(order_request)
        # Store message in session state
        st.session_state.message = f"Order placed successfully: {side.value.title()} {qty} {symbol}"
        # Force a refresh of the UI to update current orders
        st.rerun()
    except Exception as e:
        return f"Error placing order: {str(e)}"

def get_account_info():
    client = create_trading_client()
    return client.get_account()

def get_positions():
    client = create_trading_client()
    try:
        positions = client.get_all_positions()
        positions_data = []
        for position in positions:
            side = "Long" if float(position.qty) > 0 else "Short"
            positions_data.append({
                "Symbol": position.symbol,
                "Side": side,
                "Quantity": abs(float(position.qty)),
                "Market Value": f"${float(position.market_value):,.2f}",
                "Average Entry": f"${float(position.avg_entry_price):,.2f}",
                "Unrealized P/L": f"${float(position.unrealized_pl):,.2f}",
                "Current Price": f"${float(position.current_price):,.2f}"
            })
        return positions_data
    except Exception as e:
        return f"Error fetching positions: {str(e)}"

def get_orders(start_date=None, end_date=None, status=QueryOrderStatus.ALL):
    client = create_trading_client()
    try:
        request_params = GetOrdersRequest(
            status=status,
            after=start_date,
            until=end_date,
            limit=100
        )
        
        orders = client.get_orders(request_params)
        
        orders_data = []
        for order in orders:
            orders_data.append({
                "Order ID": str(order.id),  # Convert UUID to string
                "Symbol": order.symbol,
                "Side": order.side.value.title(),  # Convert to title case (Buy/Sell)
                "Quantity": order.qty,
                "Order Type": order.type.value.title(),
                "Status": order.status.value.title(),
                "Submitted At": order.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if order.submitted_at else "N/A",
                "Filled At": order.filled_at.strftime("%Y-%m-%d %H:%M:%S") if order.filled_at else "Not Filled",
                "Filled Price": f"${float(order.filled_avg_price):,.2f}" if order.filled_avg_price else "Not Filled"
            })
        return orders_data
    except Exception as e:
        return f"Error fetching orders: {str(e)}"

def get_order_by_id(order_id):
    client = create_trading_client()
    try:
        order = client.get_order_by_id(order_id)
        return order
    except Exception as e:
        return f"Error fetching order: {str(e)}"

def cancel_order(order_id):
    client = create_trading_client()
    try:
        client.cancel_order_by_id(order_id)
        # Store message in session state
        st.session_state.message = f"Order {order_id} cancelled successfully"
        # Force a refresh of the UI to update current orders
        st.rerun()
    except Exception as e:
        return f"Error cancelling order: {str(e)}"

def close_position_by_symbol(symbol):
    client = create_trading_client()
    try:
        client.close_position(symbol)
        # Store message in session state
        st.session_state.message = f"Position for {symbol} closed successfully"
        # Force a refresh of the UI to update positions
        st.rerun()
    except Exception as e:
        return f"Error closing position: {str(e)}"

def get_current_orders():
    client = create_trading_client()
    try:
        # Request only open orders
        request_params = GetOrdersRequest(
            status=QueryOrderStatus.OPEN,
            limit=100
        )
        
        orders = client.get_orders(request_params)
        
        orders_data = []
        for order in orders:
            orders_data.append({
                "Order ID": str(order.id),
                "Symbol": order.symbol,
                "Side": order.side.value.title(),
                "Quantity": order.qty,
                "Order Type": order.type.value.title(),
                "Status": order.status.value.title(),
                "Submitted At": order.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if order.submitted_at else "N/A"
            })
        return orders_data
    except Exception as e:
        return f"Error fetching current orders: {str(e)}"

def main():
    st.title("Crypto Trading Dashboard")

    # Display message from session state if there is one
    if st.session_state.message:
        st.success(st.session_state.message)
        # Clear the message after displaying it
        st.session_state.message = None

    # Trading Section
    st.header("Trading Actions")
    
    col1, col2, col3 = st.columns(3)
    
    # Buy Form
    with col1:
        st.subheader("Buy")
        buy_symbol = st.text_input("Symbol (e.g., BTC/USD)", key="buy_symbol")
        buy_qty = st.number_input("Quantity", min_value=0.0, step=0.01, key="buy_qty")
        if st.button("Buy"):
            if buy_symbol and buy_qty > 0:
                result = place_market_order(buy_symbol, buy_qty, OrderSide.BUY)
                if result:  # If there was an error, display it
                    st.write(result)
            else:
                st.write("Please enter valid symbol and quantity")

    # Sell Form
    with col2:
        st.subheader("Sell")
        sell_symbol = st.text_input("Symbol (e.g., BTC/USD)", key="sell_symbol")
        sell_qty = st.number_input("Quantity", min_value=0.0, step=0.01, key="sell_qty")
        if st.button("Sell"):
            if sell_symbol and sell_qty > 0:
                result = place_market_order(sell_symbol, sell_qty, OrderSide.SELL)
                if result:  # If there was an error, display it
                    st.write(result)
            else:
                st.write("Please enter valid symbol and quantity")

    # Close All Positions
    with col3:
        st.subheader("Close Positions")
        if st.button("Close All Positions"):
            client = create_trading_client()
            try:
                client.close_all_positions(cancel_orders=True)
                st.session_state.message = "All positions closed successfully"
                st.rerun()
            except Exception as e:
                st.write(f"Error closing positions: {str(e)}")
        
        st.subheader("Cancel Orders")
        if st.button("Cancel All Orders"):
            client = create_trading_client()
            try:
                client.cancel_orders()
                st.session_state.message = "All orders cancelled successfully"
                st.rerun()
            except Exception as e:
                st.write(f"Error cancelling orders: {str(e)}")

    # Account Information Section
    st.header("Account Information")
    account = get_account_info()
    
    col1, col2 = st.columns(2)
    
    with col1:
        account_info = {
            "Buying Power": f"${float(account.buying_power):,.2f}",
            "Cash": f"${float(account.cash):,.2f}",
            "Portfolio Value": f"${float(account.portfolio_value):,.2f}",
            "Currency": account.currency
        }
        st.write("### Basic Info")
        for key, value in account_info.items():
            st.write(f"**{key}:** {value}")
    
    with col2:
        trading_info = {
            "Pattern Day Trader": account.pattern_day_trader,
            "Trading Blocked": account.trading_blocked,
            "Transfers Blocked": account.transfers_blocked,
            "Account Blocked": account.account_blocked,
            "Multiplier": account.multiplier
        }
        st.write("### Trading Status")
        for key, value in trading_info.items():
            st.write(f"**{key}:** {value}")

    # Display Current Positions
    st.header("Current Positions")
    positions_data = get_positions()
    
    if isinstance(positions_data, list):
        if positions_data:
            st.table(pd.DataFrame(positions_data))
        else:
            st.write("No open positions")
    else:
        st.write(positions_data)

    # Order History Section
    st.header("Order History")

    # Date Range Selection
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            datetime.now() - timedelta(days=1)
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            datetime.now()
        )

    # Order Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        order_status_filter = st.selectbox(
            "Filter by Status",
            ["All Orders", "Open", "Filled", "Canceled", "Expired", "Rejected"]
        )
    
    with col2:
        side_filter = st.selectbox(
            "Filter by Side",
            ["All", "Buy", "Sell"]
        )
    
    with col3:
        symbol_filter = st.text_input("Filter by Symbol", "")

    # Convert dates to datetime
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Get orders
    orders_data = get_orders(start_datetime, end_datetime)
    
    if isinstance(orders_data, list):
        if orders_data:
            df = pd.DataFrame(orders_data)
            
            # Apply filters
            if order_status_filter != "All Orders":
                df = df[df['Status'] == order_status_filter.title()]
            
            if side_filter != "All":
                df = df[df['Side'] == side_filter.title()]
            
            if symbol_filter:
                df = df[df['Symbol'].str.contains(symbol_filter.upper(), case=False)]
            
            if not df.empty:
                st.table(df)
            else:
                st.write("No orders match the selected filters")
        else:
            st.write("No orders in the selected date range")
    else:
        st.write(orders_data)
    
    # Display Current Orders (unfilled) - Moved after Order History
    st.header("Current Orders")
    current_orders = get_current_orders()

    if isinstance(current_orders, list):
        if current_orders:
            # Create a DataFrame and add an action column
            df = pd.DataFrame(current_orders)
            
            # Display the table
            st.table(df)
            
            # Add a section to cancel a specific order
            col1, col2 = st.columns([3, 1])
            with col1:
                if current_orders:  # Check if there are any orders to select
                    order_id_to_cancel = st.selectbox(
                        "Select Order ID to cancel",
                        [order["Order ID"] for order in current_orders],
                        key="cancel_order_select"
                    )
                else:
                    st.write("No orders to cancel")
            with col2:
                if current_orders:  # Only show button if there are orders
                    if st.button("Cancel Selected Order"):
                        result = cancel_order(order_id_to_cancel)
                        if result:  # If there was an error, display it
                            st.write(result)
        else:
            st.write("No open orders")
    else:
        st.write(current_orders)  # Display error message

    # Order Management Section
    st.header("Order Management")
    order_id_to_manage = st.text_input("Enter Order ID to monitor/manage", "")

    if order_id_to_manage:
        order = get_order_by_id(order_id_to_manage)
        
        if isinstance(order, str):  # Error message
            st.error(order)
        else:
            # Create columns for order details
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### Order Details")
                st.write(f"**Symbol:** {order.symbol}")
                st.write(f"**Side:** {order.side.value.title()}")
                st.write(f"**Quantity:** {order.qty}")
                st.write(f"**Type:** {order.type.value.title()}")
                st.write(f"**Status:** {order.status.value.title()}")
            
            with col2:
                st.write("### Order Timing")
                submitted_at = order.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if order.submitted_at else "N/A"
                st.write(f"**Submitted At:** {submitted_at}")
                
                filled_at = order.filled_at.strftime("%Y-%m-%d %H:%M:%S") if order.filled_at else "Not filled yet"
                st.write(f"**Filled At:** {filled_at}")
                
                filled_price = f"${float(order.filled_avg_price):,.2f}" if order.filled_avg_price else "Not filled yet"
                st.write(f"**Filled Price:** {filled_price}")
            
            # Action buttons based on order status
            if order.status.value in ["new", "accepted", "pending_new", "accepted_for_bidding"]:
                if st.button("Cancel Order"):
                    result = cancel_order(order_id_to_manage)
                    if result:  # If there was an error, display it
                        st.write(result)
            elif order.status.value == "filled":
                if st.button(f"Close Position for {order.symbol}"):
                    result = close_position_by_symbol(order.symbol)
                    if result:  # If there was an error, display it
                        st.write(result)
            else:
                st.write(f"Order is in {order.status.value} state. No actions available.")

if __name__ == "__main__":
    main()
