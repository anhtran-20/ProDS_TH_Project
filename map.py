import pandas as pd
import numpy as np
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px

# Đọc dữ liệu từ file
metadata = pd.read_csv('states.csv')
df_usa_raw = pd.read_csv('Airline_Delay_Cause.csv')
df_usa = df_usa_raw.copy()

# Thêm cột state_id trích xuất từ cột airport_name và lấy ra cột arr_del15 đếm số lượng chuyến bay bị trễ
df_usa['airport_name']=df_usa['airport_name'].astype('string')
df_usa['state_id'] = df_usa['airport_name']

def getState(str):
    delim1 = ', '
    delim2 = ':'
    s = str[str.find(delim1) + 1 : str.find(delim2)]
    return s.replace(' ', '')
    
df_usa['state_id'] = df_usa['state_id'].apply(lambda x: getState(x))
df_usa = df_usa[df_usa['arr_del15'].notna()]
df_usa['arr_del15'] = df_usa['arr_del15'].astype(int)
df_usa['year'] = df_usa['year'].astype(int)

# Gom nhóm theo từng năm và từng bang
df_usa = df_usa[['year', 'state_id', 'arr_del15']]
df_usa = df_usa.groupby(['year', 'state_id'])['arr_del15'].agg('sum').reset_index()
df_usa2 = df_usa.copy()

# Lấy ra danh sách các bang làm hàng của dataframe
list_states = df_usa2['state_id'].drop_duplicates().sort_values().to_list()
list_years = df_usa2['year'].drop_duplicates().sort_values().to_list()

# Hàm trả về số chuyến bay trễ ở tất cả các bang khi biết năm
def count_by_state(year):
    flights = []
    sort_year = df_usa2[df_usa2['year'] == year]
    
    for state in list_states:
        a = sort_year[sort_year['state_id'] == state]['arr_del15'].to_list()
        if len(a) != 0:
            flights.append(a[0])
        else:
            flights.append(np.nan)

    return flights

# list_time chứa số chuyến bay trễ từ 2017-2022 ứng với từng năm
flights_each_year = []
for year in list_years:
    flights_each_year.append(count_by_state(year))

flights_through_years = dict(zip(list_years, flights_each_year))

# Tạo dataframe từ lights_through_years và index lấy từ list_states
# Đổi tên cột và merge với metadata
flights_each_year_df = pd.DataFrame(flights_through_years, index = list_states)
flights_each_year_df['state_id'] = flights_each_year_df.index
flights_each_year_df.columns = ['2017', '2018', '2019', '2020', '2021', '2022', 'state_id']
new_df = pd.merge(left = flights_each_year_df, right = metadata, on = 'state_id', how = 'inner')

# Thêm mảng year làm thanh trượt thời gian
year = [str(i + 2017) for i in range(6)]
column_names = ['state_id', 'state_name']

_df = pd.melt(new_df, id_vars = column_names, value_vars = year)
_df = _df.rename(columns={'variable': 'year'})
_df = _df.rename(columns={'value': 'arr_del15'})

df = _df.copy()
df['year'] = df['year'].astype(int)


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA])

app.layout = dbc.Container(html.Div([

    dbc.Row(
        dbc.Col(html.Div([
            html.H1('Flight Delay in USA Dashboard', style={'text-align': 'center', 'marginTop': 55, 'color': '#2c3e50'}),
        ]), width=12)
    ),

    dbc.Row(dbc.Col(html.Div([
        html.H3("Số chuyến bay bị trễ ở mỗi bang thay đổi như thế nào qua các năm?", style={'paddingTop': 50, 'color': '#084081'}),
        html.H5("TỪ BIỂU ĐỒ NÀY TA CÓ THỂ: so sánh giữa các bang với nhau", style={'color': '#2b8cbe'}),
        html.Hr(style={'color': "#2b8cbe", 'paddingBottom': 10, 'marginBottom': 50})
    ]))),

    dbc.Row(
            [
                dbc.Col(html.Div([
                    html.Div("Life expectancy tells us a lot about the state of a society and is a key metric worth "
                             "studying. This is why the world map shows the latest data published by the World Bank "
                             "for 'life expectancy at birth', measured in years. This metric indicates"
                             "the number of years a newborn infant would live if current mortality trends at the"
                             "time of its birth were to persist throughout its life."),
                    html.Br(),
                    html.Div("Since industrialization, life expectancy has steadily improved worldwide. "
                             "In this analysis, we look at the last few decades, from 2017 to 2022. "),
                    html.Br(),
                    html.Div(
                             "Hover over any country to view the changing life expectancy there, "
                             "or use the slider to see the change through time below the map.",
                        style={"font-weight": "bold"})]), width=3),

                # interactive map incl. slider - tạo interactive slider
                dbc.Col(html.Div([
                    html.H5("Số chuyến bay trễ chuyến tại các bang từ 2017 đến nửa đầu 2022"),
                    html.H6("California, Texas và Florida là ba bang có nhiều chuyến bay trễ chuyến nhất tại Hoa Kỳ và tương đối ổn định qua các năm, nhất là trong giai đoạn 2018-2021", style={"color": '#95a5a6'}),
                    html.Br(),
                    dcc.Graph(id="graph-with-slider", hoverData={'points': [{'customdata': 'WLD'}]}),
                    dcc.Slider(
                        min=df['year'].min(),
                        max=df['year'].max(),
                        step=None,
                        marks={
                            2017: '2017',
                            2018: '2018',
                            2019: '2019',
                            2020: '2020',
                            2021: '2021',
                            2022: '2022',
                        },
                        value=df['year'].max(),
                        id='year-slider',
                        tooltip={"placement": "bottom", "always_visible": True})
                        ]), width={"size": 8, "offset": 1})
            ]
        )
]))


# -----------------------------------------------------------------------------------------------------
# CONNECT THE GRAPHS WITH DASH COMPONENTS AND ALLOW INTERACTIVITY


# Tạo một interactive world map - choropleth map
@app.callback(
    Output(component_id='graph-with-slider', component_property='figure'),
    [Input(component_id='year-slider', component_property='value')]
)
def update_figure(selected_year):
    color_scale = ['#ffffff', '#f7fcf0', '#e0f3db', '#ccebc5', '#a8ddb5', '#7bccc4', '#4eb3d3', '#2b8cbe',
                   '#0868ac', '#084081']
    # Hiệu ứng chuyển slider sang năm khác
    filtered_df = df[df.year == selected_year].reset_index()

    # Tạo choropleth map
    world_map = px.choropleth(filtered_df, locations=filtered_df['state_id'], locationmode='USA-states',
                              color=filtered_df.arr_del15,
                              color_continuous_scale=color_scale,
                              scope = 'usa', labels={'arr_del15': 'Delay Flights'},
                              range_color=[20, 170000],
                              hover_name='state_name',
                              hover_data=['arr_del15'],
                              title = 'US Flights',
                              basemap_visible=False)
    world_map.update_layout(transition_duration=500,
                            margin=dict(l=0, r=0, b=0, t=0),
                            width=1000,
                            height=400)
    return world_map

if __name__ == '__main__':
    app.run_server(debug=True)