import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Dash
from dash.dependencies import Input, Output
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

# Group data by payment method
payment_method_revenue = sales_over_time.groupby('transaction_type').agg({
    'transaction_amount': 'sum'
}).reset_index()

# Group data by staff gender and calculate total sales amount
staff_performance = sales_over_time.groupby('received_by').agg({
    'transaction_amount': 'sum'
}).reset_index()

# Group data by item name, item type, and year_month
item_sales = sales_over_time.groupby(['item_name', 'item_type', 'year_month']).agg({
    'quantity': 'sum'
}).reset_index()

# Group data by item name and item type for initial display
initial_grouped_data = sales_over_time.groupby(['item_name', 'item_type']).agg({
    'quantity': 'sum'
}).reset_index()

# Create the Dash app
app = Dash(__name__)

app.layout = html.Div([
    html.H1('Restaurant Sales Dashboard'),

    html.Div([
        html.Label('Filter by Payment Method'),
        dcc.Dropdown(
            id='payment-filter',
            options=[{'label': method, 'value': method} for method in sales_over_time['transaction_type'].unique()],
            value=sales_over_time['transaction_type'].unique().tolist(),
            multi=True,
            clearable=False,
            style={'width': '400px', 'margin-bottom': '10px'}
        ),
    ]),

    html.Div([
        html.Label('Filter by Month'),
        dcc.Dropdown(
            id='month-filter',
            options=[{'label': 'All the time', 'value': 'All the time'}] +
                    [{'label': str(month), 'value': str(month)} for month in sales_over_time['year_month'].unique()],
            value='All the time',
            clearable=False,
            style={'width': '400px', 'margin-bottom': '10px'}
        ),
    ]),

    html.Div([
        html.Label('Filter by Time of Sale'),
        dcc.Dropdown(
            id='time-of-sale-filter',
            options=[{'label': time, 'value': time} for time in time_of_sale_order],
            value=time_of_sale_order,
            multi=True,
            clearable=False,
            style={'width': '400px', 'margin-bottom': '10px'}
        ),
    ]),

    html.Div([
        html.Label('Filter by Item Type'),
        dcc.Dropdown(
            id='item-type-filter',
            options=[{'label': item_type, 'value': item_type} for item_type in sales_over_time['item_type'].unique()],
            value=sales_over_time['item_type'].unique().tolist(),
            multi=True,
            clearable=False,
            style={'width': '400px', 'margin-bottom': '10px'}
        ),
    ]),

    html.Div([
        html.Label('Filter by Item Name'),
        dcc.Dropdown(
            id='item-name-filter',
            options=[{'label': name, 'value': name} for name in sales_over_time['item_name'].unique()],
            value=sales_over_time['item_name'].unique().tolist(),
            multi=True,
            clearable=False,
            style={'width': '400px', 'margin-bottom': '10px'}
        ),
    ]),

    html.Div([
        dcc.Graph(id='sales-trends-line-chart'),
        dcc.Graph(id='payment-method-pie-chart'),
        dcc.Graph(id='staff-performance-bar-chart'),
        dcc.Graph(id='item-preferences-bar-chart'),
        dcc.Graph(id='heatmap'),
    ]),

    dash_table.DataTable(
        id='data-table',
        columns=[{"name": i, "id": i} for i in sales_over_time.columns],
        page_size=10,
        style_table={'height': '400px', 'overflowY': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '5px'},
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
    )
])

@app.callback(
    [Output('sales-trends-line-chart', 'figure'),
     Output('payment-method-pie-chart', 'figure'),
     Output('staff-performance-bar-chart', 'figure'),
     Output('item-preferences-bar-chart', 'figure'),
     Output('heatmap', 'figure'),
     Output('data-table', 'data')],
    [Input('payment-filter', 'value'),
     Input('month-filter', 'value'),
     Input('time-of-sale-filter', 'value'),
     Input('item-type-filter', 'value'),
     Input('item-name-filter', 'value')]
)
def update_dashboard(selected_payment_methods, selected_month, selected_times, selected_item_types, selected_item_names):
    filtered_data = sales_over_time[sales_over_time['transaction_type'].isin(selected_payment_methods)]

    if selected_month != 'All the time':
        filtered_data = filtered_data[filtered_data['year_month'] == selected_month]

    filtered_data = filtered_data[filtered_data['time_of_sale'].isin(selected_times)]
    filtered_data = filtered_data[filtered_data['item_type'].isin(selected_item_types)]
    filtered_data = filtered_data[filtered_data['item_name'].isin(selected_item_names)]

    # Sales Trends Over Time
    monthly_sales = filtered_data.groupby('year_month').agg({
        'transaction_amount': 'sum'
    }).reset_index()
    monthly_sales['year_month'] = pd.to_datetime(monthly_sales['year_month'], format='%Y-%m')
    monthly_sales['3month_moving_average'] = monthly_sales['transaction_amount'].rolling(window=3).mean()

    # Create a figure for sales trends
    sales_trends_fig = make_subplots(specs=[[{"secondary_y": False}]])
    sales_trends_fig.add_trace(
        go.Scatter(x=monthly_sales['year_month'], y=monthly_sales['transaction_amount'], mode='lines+markers', name='Monthly Sales'),
        secondary_y=False,
    )
    sales_trends_fig.add_trace(
        go.Scatter(x=monthly_sales['year_month'], y=monthly_sales['3month_moving_average'], mode='lines', name='3-month Moving Average'),
        secondary_y=False,
    )
    max_month = monthly_sales.loc[monthly_sales['transaction_amount'].idxmax()]['year_month']
    max_amount = monthly_sales['transaction_amount'].max()
    sales_trends_fig.add_annotation(
        x=max_month,
        y=max_amount,
        text=f"Highest Sales: {max_amount}",
        showarrow=True,
        arrowhead=2,
        ax=20,
        ay=-40
    )
    sales_trends_fig.update_layout(
        title_text='Sales Trends Month by Month',
        xaxis_title='Month',
        yaxis_title='Total Sales Amount (in currency)',
        legend_title='Legend',
        template='plotly_white',
        xaxis=dict(
            tickmode='array',
            tickvals=monthly_sales['year_month'],
            ticktext=monthly_sales['year_month'].dt.strftime('%Y-%m'),
            dtick="M1",
            tickformat="%Y-%m",
            tickangle=-45
        ),
        yaxis=dict(
            range=[monthly_sales['transaction_amount'].min(), monthly_sales['transaction_amount'].max()]
        )
    )

    # Payment Methods
    payment_method_revenue = filtered_data.groupby('transaction_type').agg({
        'transaction_amount': 'sum'
    }).reset_index()
    payment_method_fig = px.pie(
        payment_method_revenue,
        names='transaction_type',
        values='transaction_amount',
        hover_data={'transaction_type': True, 'transaction_amount': True},
        labels={'transaction_type': 'Payment Method', 'transaction_amount': 'Total Revenue'},
        title='Impact of Payment Methods on Revenue'
    )
    payment_method_fig.update_layout(
        template='plotly_white',
        title_font=dict(size=24, family='Arial', color='black'),
        font=dict(family='Arial', size=14, color='black')
    )

    # Staff Performance
    filtered_staff_performance = filtered_data.groupby('received_by').agg({
        'transaction_amount': 'sum'
    }).reset_index()
    staff_performance_fig = px.bar(
        filtered_staff_performance, 
        x='received_by', 
        y='transaction_amount', 
        color='received_by',
        labels={'received_by': 'Staff Gender', 'transaction_amount': 'Total Sales Amount'},
        title='Total Sales Amount by Staff Gender',
        color_discrete_map={'Mr.': 'skyblue', 'Mrs.': 'salmon'}
    )
    staff_performance_fig.update_layout(
        template='plotly_white',
        title_font=dict(size=24, family='Arial', color='black'),
        xaxis_title='Staff Gender',
        yaxis_title='Total Sales Amount',
        font=dict(family='Arial', size=14, color='black'),
        showlegend=False
    )

    # Customer Preferences
    grouped_data = filtered_data.groupby(['item_name', 'item_type']).agg({
        'quantity': 'sum'
    }).reset_index()
    item_preferences_fig = px.bar(
        grouped_data,
        x='item_name',
        y='quantity',
        color='item_type',
        hover_data={'item_name': True, 'quantity': True},
        labels={'item_name': 'Item Name', 'quantity': 'Quantity Sold'},
        title='Customer Preferences for Different Items',
        category_orders={'item_type': ['Fastfood', 'Beverages']}
    )
    item_preferences_fig.update_layout(
        template='plotly_white',
        title_font=dict(size=24, family='Arial', color='black'),
        xaxis_title='Item Name',
        yaxis_title='Quantity Sold',
        legend_title='Item Type',
        font=dict(family='Arial', size=14, color='black')
    )
    item_preferences_fig.update_traces(
        hovertemplate='<b>Item Name:</b> %{x}<br><b>Quantity Sold:</b> %{y}<extra></extra>'
    )

    # Popularity of Items at Different Times of the Day
    filtered_heatmap_data = filtered_data.pivot_table(
        index='time_of_sale', 
        columns='item_name', 
        values='quantity', 
        aggfunc='sum',
        fill_value=0,
        observed=False
    )
    filtered_heatmap_data = filtered_heatmap_data.reset_index().melt(id_vars='time_of_sale', value_vars=filtered_heatmap_data.columns)
    heatmap_fig = px.density_heatmap(
        filtered_heatmap_data, 
        x='item_name', 
        y='time_of_sale', 
        z='value', 
        color_continuous_scale='Blues',
        labels={'item_name': 'Item Name', 'time_of_sale': 'Time of Sale', 'value': 'Quantity Sold'},
        title='Popularity of Items at Different Times of the Day',
        category_orders={'time_of_sale': time_of_sale_order}
    )
    heatmap_fig.update_layout(
        template='plotly_white',
        title_font=dict(size=24, family='Arial', color='black'),
        xaxis_title='Item Name',
        yaxis_title='Time of Sale',
        font=dict(family='Arial', size=14, color='black')
    )

    return (sales_trends_fig, payment_method_fig, staff_performance_fig, 
            item_preferences_fig, heatmap_fig, filtered_data.to_dict('records'))

if __name__ == '__main__':
    app.run_server(debug=True)
