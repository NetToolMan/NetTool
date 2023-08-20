import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import igraph as ig
import plotly.graph_objects as go
import random

# Create a random graph with 50 nodes and 100 edges
def create_graph():
    g = ig.Graph.Erdos_Renyi(n=50, m=100, directed=False)
    # Generate random names for nodes
    node_names = [f"Node-{i}" for i in range(0, 50)]  # Assumes node names like "Node-1", "Node-2", ...
    # Assign node names as attributes to the graph
    g.vs["name"] = node_names
    # Define node positions using a layout algorithm
    layout = g.layout("fr")  # Use the Fruchterman-Reingold layout
    return g, layout

# Create an empty figure to show when no node is selected
def create_empty_figure():
    return {
        'data': [],
        'layout': go.Layout(
            showlegend=False,
            hovermode="closest",
            margin=dict(b=0, l=0, r=0, t=0),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        )
    }

# Define a common function to create a network figure based on a graph and layout
def create_network_figure(g, layout):    
    Xn, Yn = zip(*layout)

    # Perform community detection
    communities = g.community_multilevel()
    # Assign a random color to each community
    community_colors = {}
    for idx, nodes in enumerate(communities):
        color = "#{:02x}{:02x}{:02x}".format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        for node in nodes:
            community_colors[node] = color

    # Calculate node degrees
    node_degrees = g.degree()

    # Create node and edge traces
    node_trace = go.Scatter(
        x=Xn,
        y=Yn,
        mode="markers+text",
        text=[v['name'] for v in g.vs],
        marker=dict(
            size=10,
            color=[community_colors[i] for i in range(len(g.vs))],  # Color nodes based on their community
            line_width=2,
        ),
        hovertemplate='%{text}<br>Degree: %{customdata}',  # Show name and degree on hover
        customdata=node_degrees,  # Associate degree information with each node
        textposition="top center",
        name=''
    )
    
    edge_trace = go.Scatter(
        x=[],
        y=[],
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines",
    )
    
    # Calculate edges
    edge_x = []
    edge_y = []
    for edge in g.get_edgelist():
        x0, y0 = layout[edge[0]]
        x1, y1 = layout[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    edge_trace.x = edge_x
    edge_trace.y = edge_y
    
    # Create the network figure
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode="closest",
            margin=dict(b=0, l=0, r=0, t=0),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )
    
    return fig

# Create a Dash app
app = dash.Dash(__name__)
server = app.server

# Define the layout of the app
app.layout = html.Div([
    html.H1("Interactive Network Plot"),
    
    dcc.Graph(
        id='original-network-plot',
        config={'staticPlot': False},
        style={'width': '50%', 'float': 'left'}
    ),
    dcc.Graph(
        id='subgraph-plot',
        config={'staticPlot': False},
        style={'width': '50%', 'float': 'right'}
    ),
])

# Define a global variable for the original graph
original_graph, layout = create_graph()

# Define a callback to update the original network plot
@app.callback(
    Output("original-network-plot", "figure"),
    Input("subgraph-plot", "relayoutData")
)
def update_original_network_plot(relayoutData):
    return create_network_figure(original_graph, layout)

# Define a callback to update the subgraph plot when a node is clicked
@app.callback(
    Output("subgraph-plot", "figure"),
    Input("original-network-plot", "clickData")
)
def update_subgraph_plot(clickData):
    # Create an empty subgraph figure
    subgraph_figure = create_empty_figure()
    
    if clickData is None:
        # If no node is clicked, return the empty subgraph figure
        return subgraph_figure
    
    # Extract the clicked node index
    clicked_node_index = int(clickData['points'][0]['pointIndex'])
    # Extract the neighbors of the clicked node to create a subgraph
    neighbors = original_graph.neighborhood(clicked_node_index)

    # Create a subgraph containing the clicked node and its neighbors
    subgraph = original_graph.subgraph(neighbors)
    subgraph_layout = subgraph.layout("fr")  # Use the Fruchterman-Reingold layout
    subgraph_figure = create_network_figure(subgraph,subgraph_layout)

    return subgraph_figure

if __name__ == '__main__':
    app.run_server(debug=True)