import pandas as pd
import seaborn as sns
import plotly.express as px
from plotly.subplots import make_subplots
from dash import Dash, html, dcc, Input, Output
import sys
from datetime import datetime
import statsmodels.api as sm

app = Dash()
vis_options = ['views-likes-graph', 'category-stats-bar', 'likes-dislikes', 'channel-popularity']

# Import csv and convert to dataframe, then sort by views
if __name__ == "__main__" and len(sys.argv) > 1:
    filename = str(sys.argv[1])
else:
    filename = 'Updated_US_youtube_trending_data.csv'

data = pd.read_csv(filename)
data.info()
data.sort_values(by=['view_count'])
data['publishedAt'] = pd.to_datetime(data['publishedAt'])

start_date = data['publishedAt'].min().replace(day=1)
end_date = data['publishedAt'].max().replace(day=1)
date_range = pd.date_range(start=start_date, end=end_date, freq='M')


# Set up page layout
geo_dropdown = dcc.Dropdown(options=vis_options, value=vis_options[0])

unique_category_data = data[['categoryId', 'categoryName']]
unique_category_data = unique_category_data.sort_values('categoryId', ascending=True)

unique_category_id = unique_category_data['categoryId'].unique()
unique_category_name = unique_category_data['categoryName'].unique()

app.layout = html.Div(children=[
    html.H1(children='CMSC 436 Youtube Vis'),
    geo_dropdown,
    dcc.Graph(id='views-likes-graph'),

    dcc.RangeSlider(
        id='date-slider',
        min=0,
        max=len(date_range) - 1,
        step=1,
        marks={i: date.strftime('%Y-%m') for i, date in enumerate(date_range)},
        value=[0, len(date_range) - 1],
        tooltip={'placement': 'bottom', 'always_visible': True}
    ),
    dcc.Checklist(
        id='category-checkbox',
        options=[{'label': str(unique_category_id[i]) + " - " + unique_category_name[i], 'value': unique_category_id[i]}
                 for i in range(len(unique_category_id))],
        inline=True
    ),

])

# Have user choose and display different graphs
@app.callback(
    Output(component_id='views-likes-graph', component_property='figure'),
    Input(component_id=geo_dropdown, component_property='value'),
    Input('date-slider', 'value'),
    Input('category-checkbox', 'value')
)

def update_graph(selected_vis, selected_date_range, selected_categories):

    start_date = date_range[selected_date_range[0]]
    end_date = date_range[selected_date_range[1]]
    filtered_data = data[(data['publishedAt'] >= start_date) & (data['publishedAt'] <= end_date)]

    if selected_categories:
        filtered_data = filtered_data[filtered_data['categoryId'].isin(selected_categories)]


    if(selected_vis == vis_options[0]):
        # Interactive Scatter Plot
        filtered_data['trending_date'] = pd.to_datetime(filtered_data['trending_date'])
        filtered_data['publishedAt'] = pd.to_datetime(filtered_data['publishedAt'])

        # Calculating the number of days a video has been trending by the difference between 'trending_date' and 'publishedAt'
        filtered_data['days_to_trend'] = (filtered_data['trending_date'] - filtered_data['publishedAt']).dt.days

        # Adding the hovering interactivity to the scatter plot
        fig = px.scatter(filtered_data, x='view_count', y='likes', size='comment_count', color='categoryName',
                        hover_data=['title', 'days_to_trend'],
                        title='Views to Likes', size_max=60)

        # Updating the graph size
        fig.update_layout(height=800, width=1200)
    elif(selected_vis == vis_options[1]):
            figures = [
            px.bar(filtered_data, x='categoryName', y='view_count', color='categoryName', title=f'Views per Category', log_y=True),
            px.bar(filtered_data, x='categoryName', y='likes', color='categoryName', title=f'Likes per Category', log_y=True),
            px.bar(filtered_data, x='categoryName', y='comment_count', color='categoryName', title=f'Comments per Category', log_y=True)
            ]

            fig = make_subplots(rows=len(figures), cols=1)

            for i, figure in enumerate(figures):
                for trace in range(len(figure["data"])):
                    fig.append_trace(figure["data"][trace], row=i+1, col=1)

            fig.update_layout(showlegend=False)
    elif(selected_vis == vis_options[2]):
        fig = px.scatter(filtered_data,
                        x='view_count', y=['likes', 'dislikes'],
                        trendline='ols',
                        title=f'Likes and Dislikes',
                        log_x=True,
                        log_y=True)
    elif(selected_vis == vis_options[3]):

        fig = px.sunburst(filtered_data, path=['categoryName', 'channelTitle'], values='view_count',
                        title='Sunburst Chart of View Count by Category and Channel')

        # Increase the size
        fig.update_layout(height=600, width=800)

        # Add interactive features
        fig.update_layout(margin=dict(l=0, r=0, b=0, t=40))

        fig.update_traces(
            hovertemplate='<b>%{label}</b><br>View Count: %{value}<extra></extra>'
        )
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)