import pandas as pd
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Dash, html, dcc, Input, Output
import sys
from datetime import datetime
import statsmodels.api as sm

app = Dash()
vis_options = ['Views to Likes per Video', 'User Engagement per Category', 'Likes to Dislikes per Category', 'Top Channels Popularity']

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
    html.H1(children='CMSC 436 Group Project - Youtube Popularity Visualization'),
    geo_dropdown,
    dcc.Graph(id=vis_options[0], style = {
        'margin-left': 'auto',
    }),

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
        options=[{'label': unique_category_name[i], 'value': unique_category_id[i]}
                 for i in range(len(unique_category_id))],
        inline=True
    ),

])

# Have user choose and display different graphs
@app.callback(
    Output(component_id=vis_options[0], component_property='figure'),
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
                        hover_name='title',
                        hover_data=['days_to_trend'],
                        labels={
                            "view_count": "Number of Views",
                            "likes": "Number of Likes",
                            "categoryName": "Category",
                            "comment_count": "Comment Count",
                            "days_to_trend":"Number of Days Trending"
                        },
                        size_max=60)

        # Updating the graph size and title
        fig.update_layout(
            title=dict(text='Views to Likes per Video', font=dict(size=50), automargin=True, yref='container', x=0.5),
            height=600, 
            width=1800
        )

    elif(selected_vis == vis_options[1]):
        sum_data = filtered_data[['categoryName', 'likes', 'view_count', 'comment_count']].groupby(['categoryName']).sum()
        categories = list(set(filtered_data['categoryName']))
        categories.sort()

        likes = sum_data['likes'].tolist()
        views = sum_data['view_count'].tolist()
        comments = sum_data['comment_count'].tolist()

        fig = go.Figure(
            data=[
        go.Bar(name='Views', x=categories, y=views, offsetgroup=1),
        go.Bar(name='Likes', x=categories, y=likes, offsetgroup=2),
        go.Bar(name='Comments', x=categories, y=comments, offsetgroup=3)
        ])

        fig.update_layout(
            xaxis_title="Category",
            yaxis_title="User Engagement",
            barmode='group', 
            title=dict(text='User Engagement per Category', font=dict(size=50), automargin=True, yref='container'),
            width=1900)
        fig.update_yaxes(type="log")
    elif(selected_vis == vis_options[2]):

        sum_data = filtered_data[['categoryName', 'likes', 'dislikes']].groupby(['categoryName']).sum()
        categories = list(set(filtered_data['categoryName']))
        categories.sort()

        a = sum_data['likes']
        likes = -1*a.astype(int)
        likes = likes.tolist()
        likes_labels = a.astype(int)
        likes_labels = likes_labels.tolist()

        a = sum_data['dislikes']
        dislikes = a.astype(int)
        dislikes = dislikes.tolist()

        fig = go.Figure(data=[
            go.Bar(name='Likes',
            y=categories,
            x=likes,
            text=likes_labels,
            orientation='h',
            marker=dict(color='#00b300', line=dict(
                color='rgba(0, 0, 0, 1.0)', width=0.5)),
            hovertemplate="%{y}: <br>Likes: %{text}",
            showlegend=False,
           ),
            go.Bar(name='Dislikes',
            y=categories,
            x=dislikes,
            text=dislikes,
            orientation='h',
            marker=dict(color='#ff4d4d', line=dict(
                color='rgba(0, 0, 0, 1.0)', width=0.5)),
                hovertemplate="%{y}: <br>Disikes: %{text}",
            showlegend=False,
           )
        ])

        fig.update_layout(barmode='relative')
        fig.update_layout(
            title=dict(text='Total Likes and Dislikes per Category',font=dict(size=25, family='Rockwell, monospace',color='rgb(67, 67, 67)'),               
            x=0.5
        ))

        fig.update_xaxes(
            showgrid=False,
            showticklabels=False,
            fixedrange=True,
        )
        fig.update_yaxes(
            showgrid=False,
            fixedrange=True,
        )

        fig.add_vline(x=0,
              fillcolor="black", opacity=1,
              layer="above", line_width=2,
              line_color='rgba(0, 0, 0, 1.0)',
              line_dash="solid")

    elif(selected_vis == vis_options[3]):

        fig= px.sunburst(filtered_data.head(50), path=['categoryName', 'channelTitle'], values='view_count')

        # Increase the size
        fig.update_layout(height=600, width=800)

        # Add interactive features
        fig.update_layout(margin=dict(l=0, r=0, b=0, t=40))
        fig.update_layout(
            title=dict(text='Top 50 Most Popular Channels',font=dict(size=25, family='Rockwell, monospace'),               
            x=0.5
        ))


        fig.update_traces(
            hovertemplate='<b>%{label}</b><br>View Count: %{value}<extra></extra>'
        )

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)