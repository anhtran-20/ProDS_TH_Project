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

# Hàm trích xuất 2 ký tự trong tên sân bay sang mã bang
def getState(str):
    delim1 = ', '
    delim2 = ':'
    s = str[str.find(delim1) + 1 : str.find(delim2)]
    return s.replace(' ', '')


# df_usa
# Thêm cột state_id trích xuất từ cột airport_name và lấy ra cột arr_del15 đếm số lượng chuyến bay bị trễ
df_usa['airport_name'] = df_usa['airport_name'].astype('string')
df_usa['state_id'] = df_usa['airport_name']
    
df_usa['state_id'] = df_usa['state_id'].apply(lambda x: getState(x))
df_usa = df_usa[df_usa['arr_del15'].notna()]
df_usa['arr_del15'] = df_usa['arr_del15'].astype(int)
df_usa['year'] = df_usa['year'].astype(int)

# Gom nhóm theo từng năm và từng bang
df_usa = df_usa[['year', 'state_id', 'arr_flights', 'arr_del15']]
df_usa2 = df_usa.groupby(['year', 'state_id'])[['arr_flights', 'arr_del15']].agg('sum').reset_index()
df_usa2['delay_ratio'] = round(df_usa2['arr_del15'] / df_usa2['arr_flights'] * 100, 2)

# Tạo thêm 2 dataframe df_flights và df_del15 để ghép với dataframe phía sau
df_flights = df_usa2[['year', 'state_id', 'arr_flights']]
df_del15 = df_usa2[['year', 'state_id', 'arr_del15']]


# -----------------------------------------------------------------------------------------------------
# Lấy ra danh sách các bang làm hàng của dataframe
list_states = df_usa2['state_id'].drop_duplicates().sort_values().to_list()
list_years = df_usa2['year'].drop_duplicates().sort_values().to_list()

# Hàm trả về % số chuyến bay trễ ở tất cả các bang khi biết năm
def count_by_state(year):
    flights = []
    sort_year = df_usa2[df_usa2['year'] == year]
    
    for state in list_states:
        a = sort_year[sort_year['state_id'] == state]['delay_ratio'].to_list()
        if len(a) != 0:
            flights.append(a[0])
        else:
            flights.append(np.nan)

    return flights

# list_time chứa % số chuyến bay trễ từ 2017-2022 ứng với từng năm
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
_df = _df.rename(columns={'value': 'delay_ratio'})

df = _df.copy()
df['year'] = df['year'].astype(int)

# Ghép với df_flights và df_del15
df = pd.merge(left = df, right = df_flights, on = ['state_id', 'year'], how = 'inner')
df = pd.merge(left = df, right = df_del15, on = ['state_id', 'year'], how = 'inner')


# -----------------------------------------------------------------------------------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA])

app.layout = dbc.Container(html.Div([

    dbc.Row(
        dbc.Col(html.Div([
            html.H1('Flight Delay in USA Dashboard', style={'text-align': 'center', 'marginTop': 55, 'color': '#2c3e50'}),
        ]), width=12)
    ),

    dbc.Row(dbc.Col(html.Div([
        html.H3("Tỉ lệ trễ chuyến ở mỗi bang thay đổi như thế nào qua các năm?", style={'paddingTop': 50, 'color': '#084081'}),
        html.H5("TỪ BIỂU ĐỒ NÀY TA CÓ THỂ: so sánh giữa các bang với nhau", style={'color': '#2b8cbe'}),
        html.Hr(style={'color': "#2b8cbe", 'paddingBottom': 10, 'marginBottom': 50})
    ]))),

    dbc.Row(
            [
                dbc.Col(html.Div([
                    html.Div("Qua 6 năm, tỉ lệ trễ chuyến bay ở mỗi bang chưa có dấu hiệu giảm xuống. Ngoại trừ năm 2020 do số chuyến bay giảm đột ngột nên tỉ lệ trễ chuyến cũng giảm theo, các năm còn lại chưa cho thấy sự nỗ lực của hàng không Mỹ trong việc giảm thiểu tỉ lệ các chuyến bay trễ chuyến. "),
                    html.Br(),
                    html.Div("Các khu vực hàng không trọng điểm của Hoa Kỳ tập trung ở phía Nam (khu vực có nhiều chuyến bay nhất), tại các bang California, Texas và Florida. Florida có tỉ lệ trễ chuyến cao nhất trong 3 tiểu bang ở hầu hết các năm. "),
                    html.Br(),
                    html.Div(
                             "Nhìn chung, từ 2017-2019 và 2021-nửa đầu 2022, xu hướng trễ chuyến tăng dần từ Tây sang Đông. "
                             "Năm 2020, tỉ lệ trễ chuyến tại các bang giảm đáng kể, số chuyến bay cũng giảm do ảnh hưởng của Covid-19.",
                        style={"font-weight": "bold"})]), width=3),

                # interactive map incl. slider - tạo interactive slider
                dbc.Col(html.Div([
                    html.H5("Tỉ lệ trễ chuyến tại 50 bang từ 2017 đến nửa đầu 2022"),
                    html.H6("Di chuyển chuột vào các tiểu bang để hiển thị thông tin về số chuyến bay (arr_flights), số chuyến trễ (arr_del15) và tỉ lệ trễ chuyến (delay_ratio); chọn/kéo slider bên dưới để hiển thị mốc thời gian. ", style={"color": '#95a5a6'}),
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
                              color=filtered_df.delay_ratio,
                              color_continuous_scale=color_scale,
                              scope = 'usa', labels={'delay_ratio': 'Delay ratio'},
                              range_color=[7, 35],
                              hover_name='state_name',
                              hover_data=['arr_flights', 'arr_del15', 'delay_ratio'],
                              title = 'US Flights',
                              basemap_visible=False)
    world_map.update_layout(transition_duration=500,
                            margin=dict(l=0, r=0, b=0, t=0),
                            width=1000,
                            height=400)
    return world_map

if __name__ == '__main__':
    app.run_server(debug=True)
