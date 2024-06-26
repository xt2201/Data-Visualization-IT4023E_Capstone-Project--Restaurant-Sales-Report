import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Dash
from dash.dependencies import Input, Output, State
from dash import dash_table
from plotly.subplots import make_subplots

# Load the dataset
file_path = 'Balaji Fast Food Sales.csv'
sales_over_time = pd.read_csv(file_path)

# Ensure sales_over_time['date'] is in datetime format
def parse_date(date_str):
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y'):
        try:
            return pd.to_datetime(date_str, format=fmt)
        except ValueError:
            pass
    return pd.to_datetime(date_str, errors='coerce')

sales_over_time['date'] = sales_over_time['date'].apply(parse_date)

# Drop rows with invalid dates
sales_over_time = sales_over_time.dropna(subset=['date'])

# Extract month and year for filtering
sales_over_time['year_month'] = sales_over_time['date'].dt.to_period('M').astype(str)

# Ensure 'time_of_sale' has the correct order
time_of_sale_order = ['Morning', 'Afternoon', 'Evening', 'Night', 'Midnight']
sales_over_time['time_of_sale'] = pd.Categorical(sales_over_time['time_of_sale'], categories=time_of_sale_order, ordered=True)

# Drop rows with null transaction types
sales_over_time = sales_over_time.dropna(subset=['transaction_type'])

# Ensure transaction_type has no leading/trailing spaces
sales_over_time['transaction_type'] = sales_over_time['transaction_type'].str.strip()

# Calculate Overall Performance Metrics
total_sales = sales_over_time['transaction_amount'].sum()
average_transaction_amount = sales_over_time['transaction_amount'].mean()
number_of_transactions = sales_over_time['order_id'].nunique()

# Define the monochromatic color palette
color_palette = {
    'primary': '#1f77b4',  # Dark blue
    'secondary': '#aec7e8',  # Light blue
    'accent': '#ffbb78',  # Light orange
    'neutral': '#dcdcdc',  # Light gray
    'background': '#ffffff',  # White
    'grid': '#e5e5e5',  # Light gray grid color
    'categories': ['#1f77b4', '#aec7e8', '#ffbb78', '#ff7f0e', '#2ca02c']  # Different shades for categories
}

dark_color_palette = {
    'primary': '#1f77b4',
    'secondary': '#aec7e8',
    'accent': '#ffbb78',
    'neutral': '#333333',
    'background': '#1e1e1e',
    'grid': '#444444',  # Dark gray grid color
    'categories': ['#1f77b4', '#aec7e8', '#ffbb78', '#ff7f0e', '#2ca02c']
}

# Initial theme setting
theme = 'light'

def get_color_palette(theme):
    return dark_color_palette if theme == 'dark' else color_palette

# Create Sales Trends Figures
def create_sales_trends_figures(sales_data, color_palette):
    sales_over_day_fig = px.line(
        sales_data.groupby(sales_data['date'].dt.date)['transaction_amount'].sum().reset_index(),
        x='date',
        y='transaction_amount',
        title='Sales Trends Over Day',
        color_discrete_sequence=[color_palette['primary']]
    )
    sales_over_day_fig.update_layout(
        plot_bgcolor=color_palette['background'],
        xaxis_showgrid=True,
        yaxis_showgrid=True,
        xaxis_gridcolor=color_palette['grid'],
        yaxis_gridcolor=color_palette['grid']
    )

    sales_over_week_fig = px.line(
        sales_data.groupby(sales_data['date'].dt.to_period('W').apply(lambda r: r.start_time))['transaction_amount'].sum().reset_index(),
        x='date',
        y='transaction_amount',
        title='Sales Trends Over Week',
        color_discrete_sequence=[color_palette['primary']]
    )
    sales_over_week_fig.update_layout(
        plot_bgcolor=color_palette['background'],
        xaxis_showgrid=True,
        yaxis_showgrid=True,
        xaxis_gridcolor=color_palette['grid'],
        yaxis_gridcolor=color_palette['grid']
    )

    sales_over_month_fig = px.line(
        sales_data.groupby(sales_data['date'].dt.to_period('M').apply(lambda r: r.start_time))['transaction_amount'].sum().reset_index(),
        x='date',
        y='transaction_amount',
        title='Sales Trends Over Month',
        color_discrete_sequence=[color_palette['primary']]
    )
    sales_over_month_fig.update_layout(
        plot_bgcolor=color_palette['background'],
        xaxis_showgrid=True,
        yaxis_showgrid=True,
        xaxis_gridcolor=color_palette['grid'],
        yaxis_gridcolor=color_palette['grid']
    )

    return sales_over_day_fig, sales_over_week_fig, sales_over_month_fig

# Create Interactive Line Chart with Monthly Sales Trends and 3-Month Moving Average
def create_interactive_sales_trends_fig(sales_data, color_palette):
    monthly_sales = sales_data.groupby(sales_data['date'].dt.to_period('M').apply(lambda r: r.start_time))['transaction_amount'].sum().reset_index()
    monthly_sales['3_month_MA'] = monthly_sales['transaction_amount'].rolling(window=3, min_periods=1).mean()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(x=monthly_sales['date'], y=monthly_sales['transaction_amount'], mode='lines+markers', name='Monthly Sales'),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=monthly_sales['date'], y=monthly_sales['3_month_MA'], mode='lines', name='3-Month Moving Average'),
        secondary_y=True,
    )

    fig.update_layout(
        title_text='Interactive Sales Trends Over Time',
        xaxis_title='Date',
        yaxis_title='Total Sales Amount',
        yaxis2_title='3-Month Moving Average',
        template='plotly_white',
        plot_bgcolor=color_palette['background'],
        xaxis_showgrid=True,
        yaxis_showgrid=True,
        xaxis_gridcolor=color_palette['grid'],
        yaxis_gridcolor=color_palette['grid']
    )

    return fig

# Create Figures for Operational Performance and Item-Based Sales Analysis
def create_additional_figures(sales_data, color_palette):
    payment_method_fig = px.pie(
        sales_data,
        names='transaction_type',
        values='transaction_amount',
        title='Sales by Payment Method',
        color_discrete_sequence=color_palette['categories']
    )
    payment_method_fig.update_layout(
        plot_bgcolor=color_palette['background']
    )

    staff_performance_fig = px.bar(
        sales_data.groupby('received_by')['transaction_amount'].sum().reset_index(),
        x='received_by',
        y='transaction_amount',
        title='Sales by Staff Gender',
        color='received_by',
        color_discrete_sequence=color_palette['categories']
    )
    staff_performance_fig.update_layout(
        plot_bgcolor=color_palette['background'],
        xaxis_showgrid=True,
        yaxis_showgrid=True,
        xaxis_gridcolor=color_palette['grid'],
        yaxis_gridcolor=color_palette['grid']
    )

    item_preferences_fig = px.bar(
        sales_data.groupby('item_name')['quantity'].sum().nlargest(5).reset_index(),
        x='item_name',
        y='quantity',
        title='Top-Selling Items',
        color='item_name',
        color_discrete_sequence=color_palette['categories']
    )
    item_preferences_fig.update_layout(
        plot_bgcolor=color_palette['background'],
        xaxis_showgrid=True,
        yaxis_showgrid=True,
        xaxis_gridcolor=color_palette['grid'],
        yaxis_gridcolor=color_palette['grid']
    )

    high_revenue_items_fig = px.scatter(
        sales_data.groupby('item_name')['transaction_amount'].sum().nlargest(5).reset_index(),
        x='item_name',
        y='transaction_amount',
        size='transaction_amount',
        title='High-Revenue Items',
        color='item_name',
        color_discrete_sequence=color_palette['categories']
    )
    high_revenue_items_fig.update_layout(
        plot_bgcolor=color_palette['background'],
        xaxis_showgrid=True,
        yaxis_showgrid=True,
        xaxis_gridcolor=color_palette['grid'],
        yaxis_gridcolor=color_palette['grid']
    )

    day_of_week_fig = px.bar(
        sales_data.groupby(sales_data['date'].dt.day_name(), observed=False)['transaction_amount'].sum().reset_index(),
        x='date',
        y='transaction_amount',
        title='Sales by Day of Week',
        color='date',
        color_discrete_sequence=color_palette['categories']
    )
    day_of_week_fig.update_layout(
        plot_bgcolor=color_palette['background'],
        xaxis_showgrid=True,
        yaxis_showgrid=True,
        xaxis_gridcolor=color_palette['grid'],
        yaxis_gridcolor=color_palette['grid']
    )

    return payment_method_fig, staff_performance_fig, item_preferences_fig, high_revenue_items_fig, day_of_week_fig

def create_heatmap_figure(sales_data, color_palette):
    # Create the heatmap data
    heatmap_data = sales_data.pivot_table(index='time_of_sale', columns='item_name', values='quantity', aggfunc='sum', fill_value=0, observed=False).reset_index().melt(id_vars='time_of_sale', value_vars=sales_data['item_name'].unique())

    # Create the heatmap figure
    heatmap_fig = px.density_heatmap(
        heatmap_data,
        x='item_name',
        y='time_of_sale',
        z='value',
        title='Item Popularity Heatmap',
        color_continuous_scale=px.colors.sequential.Blues
    )
    heatmap_fig.update_layout(
        plot_bgcolor=color_palette['background'],
        xaxis_showgrid=True,
        yaxis_showgrid=True,
        xaxis_gridcolor=color_palette['grid'],
        yaxis_gridcolor=color_palette['grid']
    )

    return heatmap_fig

def create_sankey_figure(sales_data, color_palette):
    sankey_data = sales_data.groupby(['item_name', 'item_type', 'transaction_type']).size().reset_index(name='count')
    all_nodes = list(sankey_data['item_name'].unique()) + list(sankey_data['item_type'].unique()) + list(sankey_data['transaction_type'].unique())
    node_indices = {node: i for i, node in enumerate(all_nodes)}
    sankey_fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color='black', width=0.5),
            label=all_nodes,
            color=color_palette['categories']
        ),
        link=dict(
            source=[node_indices[item] for item in sankey_data['item_name']] + 
                   [node_indices[item] for item in sankey_data['item_type']],
            target=[node_indices[item] for item in sankey_data['item_type']] + 
                   [node_indices[item] for item in sankey_data['transaction_type']],
            value=sankey_data['count'].tolist() * 2,
            color='rgba(31, 119, 180, 0.5)'
        )
    )])
    sankey_fig.update_layout(
        title_text='Sankey Diagram: Flow of Orders from Items to Types and Payment Methods',
        font=dict(size=10),
        template='plotly_white',
        plot_bgcolor=color_palette['background']
    )

    return sankey_fig

# Initialize the Dash app
app = Dash(__name__)
app.config.suppress_callback_exceptions = True

app.layout = html.Div([
    html.H1('Restaurant Sales Dashboard'),

    html.Div([
        html.Div([
            html.Label('Total Sales', style={'fontSize': 30}),
            html.Div(id='total-sales', style={'fontSize': 50, 'color': get_color_palette(theme)['primary']}),
        ], style={'textAlign': 'center', 'margin': '10px', 'border': '1px solid #dcdcdc', 'padding': '10px', 'backgroundColor': '#f9f9f9'}),
        
        html.Div([
            html.Label('Average Transaction Amount', style={'fontSize': 30}),
            html.Div(id='average-transaction-amount', style={'fontSize': 50, 'color': get_color_palette(theme)['primary']}),
        ], style={'textAlign': 'center', 'margin': '10px', 'border': '1px solid #dcdcdc', 'padding': '10px', 'backgroundColor': '#f9f9f9'}),
        
        html.Div([
            html.Label('Number of Transactions', style={'fontSize': 30}),
            html.Div(id='number-of-transactions', style={'fontSize': 50, 'color': get_color_palette(theme)['primary']}),
        ], style={'textAlign': 'center', 'margin': '10px', 'border': '1px solid #dcdcdc', 'padding': '10px', 'backgroundColor': '#f9f9f9'}),
    ], style={'display': 'flex', 'justify-content': 'center', 'margin-bottom': '20px'}),

    html.Div([
        html.Button('Toggle Theme', id='toggle-theme-button', n_clicks=0),
    ], style={'textAlign': 'center', 'margin-bottom': '20px'}),

    html.Div([
        html.Div([
            html.Label('Select Date Range:'),
            dcc.DatePickerRange(
                id='date-range',
                start_date=sales_over_time['date'].min(),
                end_date=sales_over_time['date'].max(),
                display_format='YYYY-MM-DD',
                style={'margin': '10px'}
            ),
        ], style={'display': 'inline-block', 'margin-right': '10px'}),
        html.Div([
            html.Label('Filter by Item Type:'),
            dcc.Dropdown(
                id='item-type-dropdown',
                options=[{'label': item_type, 'value': item_type} for item_type in sales_over_time['item_type'].unique()],
                value=sales_over_time['item_type'].unique().tolist(),
                multi=True,
                clearable=False
            ),
        ], style={'display': 'inline-block', 'margin-right': '10px'}),
        html.Div([
            html.Label('Filter by Item Name:'),
            dcc.Dropdown(
                id='item-name-dropdown',
                options=[{'label': item_name, 'value': item_name} for item_name in sales_over_time['item_name'].unique()],
                value=sales_over_time['item_name'].unique().tolist(),
                multi=True,
                clearable=False
            ),
        ], style={'display': 'inline-block', 'margin-right': '10px'}),
        html.Div([
            html.Label('Filter by Payment Method:'),
            dcc.Dropdown(
                id='payment-method-dropdown',
                options=[{'label': method, 'value': method} for method in sales_over_time['transaction_type'].unique()],
                value=sales_over_time['transaction_type'].unique().tolist(),
                multi=True,
                clearable=False
            ),
        ], style={'display': 'inline-block', 'margin-right': '10px'}),
        html.Div([
            html.Label('Filter by Transaction Amount:'),
            dcc.RangeSlider(
                id='transaction-amount-slider',
                min=sales_over_time['transaction_amount'].min(),
                max=sales_over_time['transaction_amount'].max(),
                value=[sales_over_time['transaction_amount'].min(), sales_over_time['transaction_amount'].max()],
                marks={int(sales_over_time['transaction_amount'].min()): str(int(sales_over_time['transaction_amount'].min())),
                       int(sales_over_time['transaction_amount'].max()): str(int(sales_over_time['transaction_amount'].max()))}
            ),
        ], style={'margin': '20px'}),
        html.Div([
            html.Label('Filter by Quantity:'),
            dcc.RangeSlider(
                id='quantity-slider',
                min=sales_over_time['quantity'].min(),
                max=sales_over_time['quantity'].max(),
                value=[sales_over_time['quantity'].min(), sales_over_time['quantity'].max()],
                marks={int(sales_over_time['quantity'].min()): str(int(sales_over_time['quantity'].min())),
                       int(sales_over_time['quantity'].max()): str(int(sales_over_time['quantity'].max()))}
            ),
        ], style={'margin': '20px'}),
        html.Div([
            html.Label('Select Sales Trends Over Time:'),
            dcc.Dropdown(
                id='sales-trends-dropdown',
                options=[
                    {'label': 'Sales Trends Over Day', 'value': 'day'},
                    {'label': 'Sales Trends Over Week', 'value': 'week'},
                    {'label': 'Sales Trends Over Month', 'value': 'month'},
                    {'label': 'Interactive Sales Trends Over Time', 'value': 'interactive'},
                    {'label': 'Sales by Time of Day', 'value': 'time_of_day'}
                ],
                value='day',
                clearable=False
            ),
        ], style={'margin': '20px'}),
    ], style={'display': 'flex', 'flex-wrap': 'wrap', 'justify-content': 'center', 'border': '1px solid #dcdcdc', 'padding': '10px', 'backgroundColor': '#f9f9f9'}),

    html.Div([
        html.Div([
            dcc.Graph(id='sales-trends-over-time'),
        ], style={'gridColumn': '1 / span 2', 'border': '1px solid #dcdcdc', 'padding': '10px', 'backgroundColor': '#f9f9f9'}),
        
        html.Div([
            dcc.Graph(id='payment-methods'),
        ], style={'gridColumn': '3', 'border': '1px solid #dcdcdc', 'padding': '10px', 'backgroundColor': '#f9f9f9'}),
        
        html.Div([
            dcc.Graph(id='top-selling-items'),
        ], style={'gridColumn': '1 / span 2', 'border': '1px solid #dcdcdc', 'padding': '10px', 'backgroundColor': '#f9f9f9'}),
        
        html.Div([
            dcc.Graph(id='high-revenue-items'),
        ], style={'gridColumn': '3', 'border': '1px solid #dcdcdc', 'padding': '10px', 'backgroundColor': '#f9f9f9'}),
        
        html.Div([
            dcc.Graph(id='item-popularity-heatmap'),
        ], style={'gridColumn': '1 / span 3', 'border': '1px solid #dcdcdc', 'padding': '10px', 'backgroundColor': '#f9f9f9'}),
        
        html.Div([
            dcc.Graph(id='sankey-diagram'),
        ], style={'gridColumn': '1 / span 3', 'border': '1px solid #dcdcdc', 'padding': '10px', 'backgroundColor': '#f9f9f9'}),
    ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(3, 1fr)', 'gridGap': '20px'}),
    
    dash_table.DataTable(
        id='data-table',
        columns=[{"name": i, "id": i} for i in sales_over_time.columns],
        page_size=10,
        style_table={'height': '400px', 'overflowY': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '5px'},
        style_header={'backgroundColor': get_color_palette(theme)['primary'], 'fontWeight': 'bold', 'color': 'white'}
    ),
    
    html.Button("Download Data", id="download-button"),
    dcc.Download(id="download-dataframe-csv"),
])

@app.callback(
    [Output("total-sales", "children"),
     Output("average-transaction-amount", "children"),
     Output("number-of-transactions", "children"),
     Output("sales-trends-over-time", "figure"),
     Output("payment-methods", "figure"),
     Output("top-selling-items", "figure"),
     Output("high-revenue-items", "figure"),
     Output("item-popularity-heatmap", "figure"),
     Output("sankey-diagram", "figure"),
     Output("data-table", "data")],
    [Input("toggle-theme-button", "n_clicks"),
     Input("date-range", "start_date"),
     Input("date-range", "end_date"),
     Input("transaction-amount-slider", "value"),
     Input("quantity-slider", "value"),
     Input("item-type-dropdown", "value"),
     Input("item-name-dropdown", "value"),
     Input("payment-method-dropdown", "value"),
     Input("sales-trends-dropdown", "value")]
)
def update_dashboard(toggle_n_clicks, start_date, end_date, transaction_amount_range, quantity_range, selected_item_types, selected_item_names, selected_payment_methods, selected_sales_trends):
    global theme
    global sales_over_time

    # Check for theme toggle
    if toggle_n_clicks % 2 == 1:
        theme = 'dark'
    else:
        theme = 'light'

    color_palette = get_color_palette(theme)

    filtered_data = sales_over_time[
        (sales_over_time['date'] >= start_date) & 
        (sales_over_time['date'] <= end_date) & 
        (sales_over_time['transaction_amount'] >= transaction_amount_range[0]) & 
        (sales_over_time['transaction_amount'] <= transaction_amount_range[1]) &
        (sales_over_time['quantity'] >= quantity_range[0]) &
        (sales_over_time['quantity'] <= quantity_range[1]) &
        (sales_over_time['item_type'].isin(selected_item_types)) &
        (sales_over_time['item_name'].isin(selected_item_names)) &
        (sales_over_time['transaction_type'].isin(selected_payment_methods))
    ]

    total_sales = filtered_data['transaction_amount'].sum()
    average_transaction_amount = filtered_data['transaction_amount'].mean()
    number_of_transactions = filtered_data['order_id'].nunique()

    sales_over_day_fig, sales_over_week_fig, sales_over_month_fig = create_sales_trends_figures(filtered_data, color_palette)
    interactive_sales_trends_fig = create_interactive_sales_trends_fig(filtered_data, color_palette)
    payment_method_fig, staff_performance_fig, item_preferences_fig, high_revenue_items_fig, day_of_week_fig = create_additional_figures(filtered_data, color_palette)
    heatmap_fig = create_heatmap_figure(filtered_data, color_palette)
    sankey_fig = create_sankey_figure(filtered_data, color_palette)

    if selected_sales_trends == 'day':
        sales_trends_fig = sales_over_day_fig
    elif selected_sales_trends == 'week':
        sales_trends_fig = sales_over_week_fig
    elif selected_sales_trends == 'month':
        sales_trends_fig = sales_over_month_fig
    elif selected_sales_trends == 'interactive':
        sales_trends_fig = interactive_sales_trends_fig
    elif selected_sales_trends == 'time_of_day':
        sales_trends_fig = day_of_week_fig

    return (
        f"${total_sales:,.2f}",
        f"${average_transaction_amount:,.2f}",
        f"{number_of_transactions:,}",
        sales_trends_fig,
        payment_method_fig,
        item_preferences_fig,
        high_revenue_items_fig,
        heatmap_fig,
        sankey_fig,
        filtered_data.to_dict('records')
    )

@app.callback(
    Output("download-dataframe-csv", "data"),
    [Input("download-button", "n_clicks")],
    prevent_initial_call=True,
)
def download_filtered_data(n_clicks):
    return dcc.send_data_frame(sales_over_time.to_csv, "Balaji_Fast_Food_Sales.csv")

if __name__ == '__main__':
    app.run_server(debug=True)

               
