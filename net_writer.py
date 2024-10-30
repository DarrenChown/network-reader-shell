'''__________________________________________________________________________________________________________________________

This Python File Creates a Webpage that Tabulates and Plots Network Data based on Components, Attributes and Time Series Data

__________________________________________________________________________________________________________________________'''




'''     Imports and Global Variables
_________________________________________'''
import pandas as pd
import matplotlib.pyplot as plt
import os
import pypsa
import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
app = dash.Dash(__name__) # Initialize App
loaded_network = None
loading_options = [{'label': 'Loading...', 'value': 'loading'}]
def run_dash(): app.run_server(port=5000, mode='external', debug=False)     # set the port for local host
NETWORK_FOLDER = 'SavedNetworks'            # Path to the folder where networks are stored




'''__________________________________________________________________

The Following are Methods to Read, Convert and Write: Files and Data

__________________________________________________________________'''




'''     Get the Stored Network Files (must be a .h5 file)
______________________________________________________________'''
def list_saved_networks():
    try:
        return [f for f in os.listdir(NETWORK_FOLDER) if f.endswith('.h5')]
    except FileNotFoundError:
        return []




'''     Converts the Network File to a Global Network Variable 
___________________________________________________________________'''
def load_network(network_filename):
    global loaded_network
    try:
        network = pypsa.Network()
        network_path = os.path.join(NETWORK_FOLDER, network_filename)
        network.import_from_hdf5(network_path)
        loaded_network = network
        return network
    except FileNotFoundError:
        print(f"Error: The network file '{network_filename}' does not exist.")
        return None




'''     Get the Static Data Components
___________________________________________'''
def get_all_static_data(component):     # this is normally the raw data
    if loaded_network:
        component_data = getattr(loaded_network, loaded_network.components[component]['list_name'], None)
        component_data = component_data.reset_index()   # The index is converted to a column so it can be displayed
        if isinstance(component_data, pd.DataFrame):
            sanitized_data = component_data.replace([np.inf, -np.inf, np.nan], None)
            return sanitized_data
    return None




'''     Get the Time Series / Varying Data
_______________________________________________'''
def get_varying_data(component, attr):
    if loaded_network:
        varying_data = getattr(loaded_network, f'{loaded_network.components[component]["list_name"]}_t', None)      # Varying data components normally end with '_t' (links_t)
        if isinstance(varying_data, pd.DataFrame):
            if attr in varying_data.columns:    # Attribute values in Components are Seperated for display unlike the Static Data
                varying_attr_data = varying_data[[attr]].replace([np.inf, -np.inf, np.nan], None)
                varying_attr_data = varying_attr_data.reset_index()
                return varying_attr_data
        elif isinstance(varying_data, dict):
            if attr in varying_data:
                attribute_data = varying_data[attr]                 # Get the data for the selected attribute
                if isinstance(attribute_data, pd.DataFrame):
                    attribute_data = attribute_data.replace([np.inf, -np.inf, np.nan], None)    # 'NaN', 'Infinity' and 'Negative Infinity' turn into 'None' (Removes Some Errors)
                    attribute_data = attribute_data.reset_index()
                    return attribute_data
                return attribute_data       # If not a DataFrame, just return the raw data (assuming it's clean)
        print(f"Error: The varying data for '{attr}' in component '{component}' is not available in the expected format.")
    return None # No Data




'''________________________________________________________________________________

The Following are Dash Functions to Set the Layout and Functionality of the Webpage

________________________________________________________________________________'''




'''     This is the HTML format for the Dash Webpage
_________________________________________________________'''
app.layout = html.Div([
    html.H1("PyPSA Network Viewer"),
    html.Div([
        html.Div([                      # Network Selection
            html.Label(
                "Network:", 
                style={
                    'display': 'block', 
                    'textAlign': 'left'
                }
            ),
            dcc.Dropdown(
                id='network-dropdown',
                options=[{
                    'label': net, 
                    'value': net
                } for net in list_saved_networks()],
                placeholder="Select a network...",
                style={'width': '100%'}
            )
        ], 
        style={
            'flex': '1', 
            'minWidth': '50px', 
            'maxWidth': '150px', 
            'marginRight': '10px'
            }
        ),
        dcc.Loading(                    # Component Selection
            id="loading-components",
            type="default",
            children=[
                html.Div([
                    html.Label(
                        "Component:", 
                        id='component-label', 
                        style={
                            'display': 'none', 
                            'textAlign': 'left'
                        }
                    ),
                    dcc.Dropdown(
                        id='component-dropdown', 
                        placeholder="Select a component...", 
                        style={
                            'width': '100%', 
                            'display': 'none'
                        }
                    )
                ], 
                style={
                    'flex': '1', 
                    'minWidth': '180px', 
                    'maxWidth': '300px', 
                    'marginRight': '10px'
                    }
                )
            ]
        ),
        html.Div([                      # Data Type Selection (Static / Time Series)
            html.Label(
                "Data Type:", 
                id='datatype-label', 
                style={
                    'display': 'none', 
                    'textAlign': 'left'
                }
            ),
            dcc.Dropdown(
                id='datatype-dropdown', 
                options=[
                    {
                        'label': 'Static Data', 
                        'value': 'static'
                    },
                    {
                        'label': 'Varying Data', 
                        'value': 'varying'
                    }
                ],
                value='static',
                style={
                    'width': '100%', 
                    'display': 'none'
                }
            )
        ],
        style={
            'flex': '1', 
            'minWidth': '50px', 
            'maxWidth': '120px', 
            'marginRight': '10px'
            }
        ),
        
        dcc.Loading(                    # Attribute Selection
            id="loading-attributes",
            type="default",
            children=[
                html.Div([
                    html.Label(
                        "Attribute:", 
                        id='attribute-label', 
                        style={
                            'display': 'none', 
                            'textAlign': 'left'
                        }
                    ),
                    dcc.Dropdown(
                        id='attribute-dropdown', 
                        placeholder="Select an attribute...", 
                        style={
                            'width': '100%', 
                            'display': 'none'
                        }
                    )
                ], 
                style={
                    'flex': '1', 
                    'minWidth': '100px', 
                    'maxWidth': '150px', 
                    'marginRight': '10px'
                    }
                )
            ]
        ),

        html.Div([                  # Display Type Selection (Table / Plot)
            html.Label(
                "Display Type:", 
                id='displaytype-label', 
                style={
                    'display': 'none', 
                    'textAlign': 'left'
                }
            ),
            dcc.Dropdown(
                id='displaytype-dropdown', 
                options=[
                    {
                        'label': 'Table', 
                        'value': 'table'
                        },
                    {
                        'label': 'Plot', 
                        'value': 'plot'
                        }
                ],
                value='table',
                style={
                    'width': '100%', 
                    'display': 'none'
                }
            )
        ],
        style={
            'flex': '1', 
            'minWidth': '50px', 
            'maxWidth': '150px', 
            'marginRight': '10px'
            }
        )
    ],
    style={
        'display': 'flex', 
        'alignItems': 'flex-start', 
        'marginTop': '10px'
        }
    ),

    html.Br(),

    dcc.Loading(                    # Output (Output / Graph) = (Table / Plot)
        id="loading-output",
        type="default",
        children=[            
            html.Div(
                id='data-output', 
                style={
                    'display': 'none', 
                    'margin-top': '20px'
                }
            ),
            dcc.Graph(
                id='data-graph',
                style={
                    'display': 'none', 
                    'margin-top': '20px'
                }
            )
        ]
    )
])




'''______________________________________________________________________________________________________________________

The Following are Callbacks that Dash Uses to Dynamically Change the Webpage based on Conditions like Selecting Dropdowns

______________________________________________________________________________________________________________________'''





'''     Adds a list of Components to the Component Dropdown when the Network is Selected
_____________________________________________________________________________________________'''
@app.callback(
    Output('component-dropdown', 'options'),
    [Input('network-dropdown', 'value')]
)
def load_selected_network(network_filename):
    if network_filename:
        network = load_network(network_filename)
        if network:
            components = list(network.components.keys())
            component_options = [{'label': comp, 'value': comp} for comp in components]
            return component_options
        else:
            return [] 
    return []




'''     The Component Dropdown is Shown When Values are Added to it
________________________________________________________________________'''
@app.callback(
    [Output('component-dropdown', 'style'), 
     Output('component-label', 'style'),
     Output('datatype-dropdown', 'style'),
     Output('datatype-label', 'style')],
    [Input('component-dropdown', 'options')]
)
def show_component_dropdown(component_options):
    if component_options:
        return {'display': 'block'}, {'display': 'block'}, {'display': 'block'}, {'display': 'block'}
    else:
        return {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}
    



'''     Shows or Hides Multiple Dropdowns and Sets Display to 'table' when the Data Type Dropdown is Changed
_________________________________________________________________________________________________________________'''
@app.callback(
    [Output('attribute-dropdown', 'style'), 
     Output('attribute-label', 'style'), 
     Output('displaytype-dropdown', 'style'),
     Output('displaytype-label', 'style'),
     Output('displaytype-dropdown', 'value')],
    [Input('datatype-dropdown', 'value')]
)
def toggle_varying_data_elements(data_type):
    if data_type == 'varying':
        return {'display': 'block'}, {'display': 'block'}, {'display': 'block'}, {'display': 'block'}, 'table'
    else:
        return {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}, 'table'




'''     Updates the Attribute Values when a Time Series Component is Chosen
________________________________________________________________________________'''
@app.callback(
    Output('attribute-dropdown', 'options'),
    [Input('component-dropdown', 'value'), 
     Input('datatype-dropdown', 'value')]
)
def load_varying_attributes(selected_component, data_type):
    if data_type == 'varying' and selected_component:

        component_data = getattr(loaded_network, f'{loaded_network.components[selected_component]["list_name"]}_t', None)
        
        if isinstance(component_data, dict):
            return [{'label': attr, 'value': attr} for attr in component_data.keys()]

        elif isinstance(component_data, pd.DataFrame):
            return [{'label': attr, 'value': attr} for attr in component_data.columns]

    return []




'''     This Callback Sets the Table and Plot for both Static and Varying Data
___________________________________________________________________________________'''
@app.callback(
    [Output('data-output', 'children'),
    Output('data-graph', 'figure')],
    [Input('network-dropdown', 'value'), 
     Input('component-dropdown', 'value'), 
     Input('datatype-dropdown', 'value'), 
     Input('attribute-dropdown', 'value'), 
     Input('displaytype-dropdown', 'value')]
)
def display_data(network_filename, selected_component, data_type, selected_attribute, view_type):
    if network_filename:
        if selected_component:
            if data_type == 'static':
                static_data = get_all_static_data(selected_component)
                if static_data is not None:
                    return html.Pre(static_data.to_string(index=False)), {}  # Display static data as a table
                return "No static data available.", {}
            elif data_type == 'varying':
                varying_data = get_varying_data(selected_component, selected_attribute)
                if varying_data is not None and len(varying_data.columns[1:]) > 0:
                    if view_type == 'table':
                        return html.Pre(varying_data.to_string(index=False)), {}  # Display varying data as a table
                    elif view_type == 'plot':
                        x_axis_data = varying_data.iloc[:, 0]  # Use the first column as x-axis
                        y_columns = varying_data.columns[1:]  # All other columns for y-axis
                        if not x_axis_data.empty and not y_columns.empty:
                            fig = go.Figure()
                            for column in y_columns:
                                fig.add_trace(go.Scatter(
                                    x=x_axis_data,
                                    y=varying_data[column],
                                    mode='lines+markers',
                                    name=column
                                ))
                            fig.update_layout(
                                title=f"Varying Data for {selected_component}",
                                xaxis_title="Date",
                                yaxis_title="Values",
                                template="plotly_white"
                            )
                            return html.Div(), fig 
                        else:
                            return f"Could not find data to plot Attribute:'{selected_attribute}' from Component:'{selected_component}'", html.Div()
                elif selected_attribute is None:
                    return "", html.Div()
                else:
                    return f"'{selected_attribute}' from '{selected_component}' contains only the Index / Snapshot.", html.Div()
                return f"No varying data available for: '{selected_attribute}' from '{selected_component}'.", html.Div()
        return "", html.Div()
    return "", html.Div()



'''     Hide and Show the Plot or Table (not shown at the same time)
__________________________________________________________________________'''
@app.callback(
    [Output('data-output', 'style'), 
     Output('data-graph', 'style')],
    [Input('displaytype-dropdown', 'value')]
)
def show_component_dropdown(display_options):
    if display_options == "table":
        return {'display': 'block'}, {'display': 'none'}
    elif display_options == "plot":
        return {'display': 'none'}, {'display': 'block'}
    else:
        return {'display': 'none'}, {'display': 'none'}
    



if __name__ == '__main__':
    app.run_server(debug=True)
