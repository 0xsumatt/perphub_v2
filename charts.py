import altair as alt

def create_bar_chart(df, x_column, y_column, title="", color_scheme=None):
    # If a color scheme is provided, use it for the color encoding
    if color_scheme:
        color_encode = alt.Color(f'{x_column}:N', scale=alt.Scale(domain=list(color_scheme.keys()), range=list(color_scheme.values())))
    else:
        color_encode = f'{x_column}:N'
    
    chart = alt.Chart(df).mark_bar().encode(
        x=x_column,
        y=y_column,
        color=color_encode,
        tooltip=[x_column, y_column]
    ).properties(title=title)
    
    return chart

def create_line_chart(df, x_column, y_column, title="", color=None, color_scheme=None):
    
    # Base chart setup with mark_line()
    chart = alt.Chart(df).mark_line()
    
    # If color and color_scheme are provided, filter the domain
    if color and color_scheme:
        # Get unique categories from the dataframe
        unique_categories = df[color].unique().tolist()
        
        # Filter color_scheme to only include these categories
        filtered_color_scheme = {cat: color_scheme[cat] for cat in unique_categories if cat in color_scheme}
        
        chart = chart.encode(
            x=x_column,
            y=y_column,
            color=alt.Color(color, 
                            scale=alt.Scale(domain=list(filtered_color_scheme.keys()), 
                                            range=list(filtered_color_scheme.values()))),
            tooltip=[x_column, y_column, color]
        )
    # Default encoding without specific color
    else:
        chart = chart.encode(
            x=x_column,
            y=y_column,
            tooltip=[x_column, y_column]
        )
    
    # Add title and make the chart interactive
    chart = chart.properties(title=title).interactive()
    
    return chart




def create_interactive_chart(df_bybit, exchange_df, width=700, height=700):
    # Candlestick Chart
    base = alt.Chart(df_bybit).encode(x='timestamp:T').properties(width=width, height=height)
    candlestick = base.mark_rule().encode(
        y=alt.Y('opening_price:Q', axis=alt.Axis(title='Price')),
        y2='closing_price:Q',
        color=alt.condition('datum.opening_price < datum.closing_price', alt.value('green'), alt.value('red'))
    )

    # Plot Trades
    trades = alt.Chart(exchange_df).mark_circle().encode(
        x='timestamp:T',
        y=alt.Y('price:Q', axis=alt.Axis(title='')),  # Removing the y-axis title for trades
        color=alt.condition(
            (alt.datum.side == 'B') | (alt.datum.side == 'bid') | (alt.datum.isBid == "true"),  # Updated condition
            alt.value('green'),  # Color if any of the conditions is true
            alt.value('red')     # Color otherwise
        ),
        tooltip=['symbol:N', 'price:Q', 'side:N']
    ).properties(width=width, height=height)

    # Layer Charts
    combined_chart = (candlestick + trades).interactive()  

    return combined_chart
