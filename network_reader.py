'''__________________________________________________________________________________________________________________________

This Python File Creates a Webpage that Tabulates and Plots Network Data based on Components, Attributes and Time Series Data

Developed by Darren Chown (https://github.com/DarrenChown)

__________________________________________________________________________________________________________________________'''


'''     Imports and Global Variables
_________________________________________'''
# Extension Imports
import pandas as pd
import os
import pypsa
import numpy as np
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import threading as th
import webbrowser as wb
from pathlib import Path

# Global Variables
loaded_network = None
compare_network = None

Default_Folder = ""
ROOT_DIRECTORY = Path(__file__).parent
loading_options = [{'label': 'Loading...', 'value': 'loading'}]




'''_____________________________________________

The Following Configure the Host and Run the App

_____________________________________________'''
app = dash.Dash(__name__)
def run_dash(): 
    app.run(port=5000,  debug=False)
def open_app(defaultFolder):
    global Default_Folder
    Default_Folder = Path(defaultFolder)
    # print(f"NETWORK_FOLDER set to: {NETWORK_FOLDER}")
    app.layout['folder-dropdown'].value = Default_Folder.name
    dash_thread = th.Thread(target=run_dash, daemon=True)
    dash_thread.start()
    wb.open("http://127.0.0.1:5000/")




'''_________________________________________________________________

The Following are Methods to Read, Convert and Write: Files and Data

_________________________________________________________________'''




'''     Get the Stored Network Files (must be a .h5 file)
______________________________________________________________'''
def list_saved_networks(network_folder):
    """Get a list of saved network files in the specified folder (must be .h5 files)."""
    if network_folder:
        network_path = Path(network_folder)
        if network_path.exists():
            return [f.name for f in network_path.iterdir() if f.suffix == '.h5']
        else:
            print("Error: The specified network folder does not exist.")
            return []
    else:
        print("Warning: No default network folder specified.")
        return ["No Default"]


class NetworkData:
    def __init__(self, network):
        self.network = network

    '''     Converts the Network File to a Global Network Variable 
    ___________________________________________________________________'''
    def load_network(self, network_folder, network_filename):
        try:
            network = pypsa.Network()
            network_path = os.path.join(network_folder, network_filename)
            network.import_from_hdf5(network_path)
            self.network = network
            return network
        except FileNotFoundError:
            print(f"Error: The network file '{network_filename}' does not exist in '{network_folder}'.")
            return None
        except Exception as e:
            print(f"An error occurred while loading the network: {e}")
            return None




    '''     Get the Static Data Components
    ___________________________________________'''
    def get_all_static_data(self, component):
        if self.network:
            component_data = getattr(self.network, self.network.components[component]['list_name'], None)
            component_data = component_data.reset_index()  # Convert index to a column
            if isinstance(component_data, pd.DataFrame):
                sanitized_data = component_data.replace([np.inf, -np.inf, np.nan], None)
                return sanitized_data
        return None


    def get_varying_attributes(self, component):
        """Retrieve varying attributes for a specific component."""
        if self.network:
            component_data = getattr(self.network, f'{self.network.components[component]["list_name"]}_t', None)
            if isinstance(component_data, dict):
                return [{'label': attr, 'value': attr} for attr in component_data.keys()]
            elif isinstance(component_data, pd.DataFrame):
                return [{'label': attr, 'value': attr} for attr in component_data.columns]
        return []
    

    '''     Get the Time Series / Varying Data
    _______________________________________________'''
    def get_varying_data(self, component, attr):
        if self.network:
            varying_data = getattr(self.network, f"{self.network.components[component]['list_name']}_t", None)
            if isinstance(varying_data, pd.DataFrame):
                if attr in varying_data.columns:
                    varying_attr_data = varying_data[[attr]].replace([np.inf, -np.inf, np.nan], None)
                    varying_attr_data = varying_attr_data.reset_index()
                    return varying_attr_data
            elif isinstance(varying_data, dict) and attr in varying_data:
                attribute_data = varying_data[attr]
                if isinstance(attribute_data, pd.DataFrame):
                    attribute_data = attribute_data.replace([np.inf, -np.inf, np.nan], None)
                    attribute_data = attribute_data.reset_index()
                    return attribute_data
                return attribute_data
        return None





'''________________________________________________________________________________

The Following are Dash Functions to Set the Layout and Functionality of the Webpage

________________________________________________________________________________'''




'''     This is the HTML format for the Dash Webpage
_________________________________________________________'''
app.layout = html.Div([
    html.Div([
        html.Div([                      # Network Selection
            html.Label(
                "Network Folder:", 
                style={
                    'display': 'block', 
                    'textAlign': 'left'
                }
            ),
            dcc.Dropdown(
                id='folder-dropdown',
                options=[{'label': folder.name, 'value': folder.name} for folder in ROOT_DIRECTORY.iterdir() if folder.is_dir()],
                placeholder="Select a folder...",
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
                options=[], 
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
        ),

        html.Div([                      # Network Compare Selection
            html.Label(
                "Compare Network:", 
                id='networkcompare-label',
                style={
                    'display': 'none', 
                    'textAlign': 'left'
                }
            ),
            dcc.Dropdown(
                id='networkcompare-dropdown',
                options=[], 
                placeholder="Select a network...",
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

    # html.Br(),

    dcc.Loading(
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
            html.Div(
                style={
                    'display': 'flex',
                    'flex-grow': '1',
                    'height': '90vh' 
                },
                children=[
                    dcc.Graph(
                        id='data-graph',
                        style={
                            'display': 'none',
                            'width': '100%',
                            'height': '90%',
                            'margin-top': '20px'
                        },
                        config={
                            'responsive': True
                        }
                    )
                ]
            )
        ]
    )
])




'''______________________________________________________________________________________________________________________

The Following are Callbacks that Dash Uses to Dynamically Change the Webpage based on Conditions like Selecting Dropdowns

______________________________________________________________________________________________________________________'''

loaded_network_data = NetworkData(None)
compare_network_data = NetworkData(None)

'''     Adds a list of Networks based on the Selected Folder
_________________________________________________________________'''
@app.callback(
    Output('network-dropdown', 'options'),
    Input('folder-dropdown', 'value')
)
def update_network_dropdown(selected_folder):
    if selected_folder is None:
        return []
    global NETWORK_FOLDER
    NETWORK_FOLDER = ROOT_DIRECTORY / selected_folder
    network_files = [f.name for f in NETWORK_FOLDER.iterdir() if f.suffix == '.h5']
    return [{'label': net, 'value': net} for net in network_files]


@app.callback(
    [Output('networkcompare-dropdown', 'style'),
     Output('networkcompare-label', 'style'),
     Output('networkcompare-dropdown', 'options'),
     Output('networkcompare-dropdown', 'value')],
    [Input('displaytype-dropdown', 'value'),
     Input('folder-dropdown', 'value'),
     Input('network-dropdown', 'value')]
)
def show_compare(view_type, selected_folder, network_select):
    if selected_folder is None:
        return []
    if view_type == 'plot':
        global NETWORK_FOLDER
        NETWORK_FOLDER = ROOT_DIRECTORY / selected_folder
        network_files = [f.name for f in NETWORK_FOLDER.iterdir() if f.suffix == '.h5']
        return {'display': 'block'}, {'display': 'block'}, [{'label': net, 'value': net} for net in network_files], network_select
    return {'display': 'none'}, {'display': 'none'}, [], network_select
    



'''     Ensures Dropdowns are Hidden when a New Folder is Selected
_______________________________________________________________________'''
@app.callback(
    Output('datatype-dropdown', 'value'),
    Input('folder-dropdown', 'value')
)
def change_folder(new_folder):
    if new_folder:
        return 'static'



'''     Adds a list of Components to the Component Dropdown when the Network is Selected
_____________________________________________________________________________________________'''
@app.callback(
    Output('component-dropdown', 'options'),
    [Input('network-dropdown', 'value'),
     Input('folder-dropdown', 'value'),
     Input('networkcompare-dropdown', 'value')]
)
def load_selected_network(network_filename, network_foldername, compare_filename):
    primary_components = set()
    if network_filename:
        network = loaded_network_data.load_network(network_foldername, network_filename)
        if network:
            primary_components = set(network.components.keys())
    compare_components = set()
    if compare_filename:
        compare_network = compare_network_data.load_network(network_foldername, compare_filename)
        if compare_network:
            compare_components = set(compare_network.components.keys())
    if primary_components and compare_components:
        common_components = primary_components.intersection(compare_components)
    else:
        common_components = primary_components or compare_components
    component_options = [{'label': comp, 'value': comp} for comp in common_components]
    return component_options





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
        return loaded_network_data.get_varying_attributes(selected_component)
    return []



'''     This Callback Sets the Table and Plot for both Static and Varying Data
___________________________________________________________________________________'''

def create_plot(data, x_axis_data, y_columns, title_suffix=""):
    fig = go.Figure()
    for column in y_columns:
        fig.add_trace(go.Scatter(
            x=x_axis_data,
            y=data[column],
            mode='lines',
            name=f"{column} {title_suffix}"
        ))
    return fig


@app.callback(
    [Output('data-output', 'children'),
     Output('data-graph', 'figure')],
    [Input('network-dropdown', 'value'), 
     Input('component-dropdown', 'value'), 
     Input('datatype-dropdown', 'value'), 
     Input('attribute-dropdown', 'value'), 
     Input('displaytype-dropdown', 'value'),
     Input('networkcompare-dropdown', 'value')]
)
def display_data(network_filename, selected_component, data_type, selected_attribute, view_type, compare_filename):
    empty_fig = go.Figure()
    empty_fig.update_layout(
        title="No Data Available",
        xaxis_title="",
        yaxis_title="",
        template="plotly_white",
        autosize=True
    )
    if not network_filename:
        return "", empty_fig
    if selected_component:
        if data_type == 'static':
            static_data = loaded_network_data.get_all_static_data(selected_component)
            if static_data is not None:
                return html.Pre(static_data.to_string(index=False)), empty_fig
            return "No static data available.", empty_fig
        elif data_type == 'varying':            
            fig = go.Figure()
            primary_data = loaded_network_data.get_varying_data(selected_component, selected_attribute)
            if view_type == 'table':
                return html.Pre(primary_data.to_string(index=False)), empty_fig
            if view_type == 'plot':
                if primary_data is not None and len(primary_data.columns) > 1:
                    x_axis_data = primary_data.iloc[:, 0]
                    y_columns = primary_data.columns[1:]
                    for column in y_columns:
                        fig.add_trace(go.Scatter(
                            x=x_axis_data,
                            y=primary_data[column],
                            mode='lines',
                            name=f"{column} ({network_filename})"
                        ))
                if compare_filename and network_filename != compare_filename:
                    print(f"Loading comparison data for network: {compare_filename}")
                    compare_data = compare_network_data.get_varying_data(selected_component, selected_attribute)
                    if compare_data is not None and len(compare_data.columns) > 1:
                        x_axis_data_compare = compare_data.iloc[:, 0]
                        y_columns_compare = compare_data.columns[1:]
                        for column in y_columns_compare:
                            fig.add_trace(go.Scatter(
                                x=x_axis_data_compare,
                                y=compare_data[column],
                                mode='lines',
                                name=f"{column} ({compare_filename})"
                            ))
                if not fig.data:
                    return "No data available for the selected component and attribute.", empty_fig
                fig.update_layout(
                    title=f"Comparison of {selected_component} Data",
                    xaxis_title="Date",
                    yaxis_title="Values",
                    template="plotly_white",
                    autosize=True
                )
                return html.Div(), fig
    return "", empty_fig


'''     Hide and Show the Plot or Table (not shown at the same time)
__________________________________________________________________________'''
@app.callback(
    [Output('data-output', 'style'), 
     Output('data-graph', 'style')],
    [Input('displaytype-dropdown', 'value'),
     Input('datatype-dropdown', 'value'),
     Input('attribute-dropdown', 'value')]
)
def show_component_dropdown(display_select, datatype_select, attribute_select):
    if datatype_select == "varying" and not attribute_select:
            return {'display': 'none'}, {'display': 'none', 'width': '0%', 'height': '0%', 'margin-top': '20px'}
    if display_select == "table":        
        return {'display': 'block'}, {'display': 'none', 'width': '0%', 'height': '0%', 'margin-top': '20px'}
    elif display_select == "plot":
        return {'display': 'none'}, {'display': 'block', 'width': '100%', 'height': '100%', 'margin-top': '20px'}
    else:
        return {'display': 'none'}, {'display': 'none'}
    



if __name__ == '__main__':
    app.run_server(debug=True)
