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
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import threading as th
import webbrowser as wb
from pathlib import Path

# Global Variables
loaded_network = None
compare_network = None
hidden = {'display': 'none'}
visible = {'display': 'block'}


Default_Folder = ""
ROOT_DIRECTORY = Path(__file__).parent
loading_options = [{'label': 'Loading...', 'value': 'loading'}]




'''_____________________________________________

The Following Configure the Host and Run the App

_____________________________________________'''
app = dash.Dash(__name__, external_stylesheets=[
    "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"
])
def run_dash(): 
    app.run(port=5000,  debug=False)
def open_app(defaultFolder):
    global Default_Folder
    Default_Folder = Path(defaultFolder)
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
    def __init__(self):
        # Dictionary to hold multiple networks
        self.networks = {}

    '''     Load and store multiple networks by filename 
    ___________________________________________________________________'''
    def load_network(self, network_folder, network_filename):
        try:
            # Initialize a new PyPSA Network and load data
            network = pypsa.Network()
            network_path = os.path.join(network_folder, network_filename)
            network.import_from_hdf5(network_path)
            
            # Store the network in the dictionary with the filename as the key
            self.networks[network_filename] = network
            print(f"Network '{network_filename}' loaded successfully.")
        except FileNotFoundError:
            print(f"Error: The network file '{network_filename}' does not exist in '{network_folder}'.")
            self.networks[network_filename] = None
        except Exception as e:
            print(f"An error occurred while loading the network: {e}")
            self.networks[network_filename] = None

    '''     Get a specific network by filename
    ___________________________________________________________________'''
    def get_network(self, network_filename):
        # Return the network object if it exists, otherwise return None
        return self.networks.get(network_filename)

    '''     Get static data from a specific network by component
    ___________________________________________________________________'''
    def get_all_static_data(self, network_filename, component):
        network = self.get_network(network_filename)
        if network:
            component_data = getattr(network, network.components[component]['list_name'], None)
            if isinstance(component_data, pd.DataFrame):
                sanitized_data = component_data.replace([np.inf, -np.inf, np.nan], None)
                return sanitized_data.reset_index()  # Convert index to a column
        return None


    def get_varying_attributes(self, network_filename, component):
        """Retrieve varying attributes for a specific component in a specific network."""
        network = self.get_network(network_filename)
        if network and component in network.components:
            # Access the component's time-varying data
            component_data = getattr(network, f'{network.components[component]["list_name"]}_t', None)
            if isinstance(component_data, dict):
                return list(component_data.keys())  # Return list of keys
            elif isinstance(component_data, pd.DataFrame):
                return list(component_data.columns)  # Return list of DataFrame columns
        return None  # Return None if no varying attributes found

    

    '''     Get the Time Series / Varying Data
    _______________________________________________'''
    def get_varying_data(self, network_filename, component, attr):
        """Retrieve time series data for a specific attribute of a component in a specific network."""
        network = self.get_network(network_filename)
        if network:
            varying_data = getattr(network, f"{network.components[component]['list_name']}_t", None)
            
            # Case 1: varying_data is a DataFrame
            if isinstance(varying_data, pd.DataFrame):
                if attr in varying_data.columns:
                    varying_attr_data = varying_data[[attr]].replace([np.inf, -np.inf, np.nan], None)
                    varying_attr_data = varying_attr_data.reset_index()
                    return varying_attr_data
            
            # Case 2: varying_data is a dictionary
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

LabelStyle = {
    'display': 'block', 
    'textAlign': 'left',
    'marginRight': '10px',
    'fontSize': '20px',
    'fontWeight': 'bold', 
    'color': '#ffffff', 
    'fontFamily': 'Roboto, sans-serif'
}

DropdownStyle={
    'width': '100%',
    'marginRight': '10px',
    'fontFamily': 'Roboto, sans-serif',
    'fontSize': '15px'
}

TinyBoxStyle={
    'flex': '1',
    'display': 'flex', 
    'alignItems': 'center',
    'marginBottom': '10px',
    'borderRadius': '5px'
}

DropdownContain={
    'marginRight': '10px',
    'borderRadius': '15px',
    'padding': '15px',
    'minWidth': '50px', 
    'maxWidth': '500px', 
    'flex': '1', 
    'background': '#296900',
    'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.2)'
}

BigBoxStyle={
    'marginTop': '10px',
    'borderRadius': '15px',
    'padding': '20px',
    'alignItems': 'center',
    'display': 'flex',
    'background': 'linear-gradient(to right, #7ebf5f, #5eb4bf)',
    'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.2)'
}

ButtonStyle={
    'marginRight': '10px',
    'width': '100%',
    'height': '40px',
    'fontFamily': 'Roboto, sans-serif',
    'fontSize': '14px',
    'borderRadius': '5px',
    'verticalAlign': 'middle',
    'fontSize': '15px',
    'cursor': 'pointer'
}

DoneButtonStyle={
    'marginTop': '10px',
    'backgroundColor': '#4CAF50',
    'color': 'white',
    'padding': '5px 10px',
    'border': 'none',
    'borderRadius': '3px',
    'cursor': 'pointer'
}

CheckboxStyle={
    'position': 'absolute',
    'top': '40px',
    'left': '93px',
    'backgroundColor': 'white',
    'border': '1px solid #ccc',
    'borderRadius': '5px',
    'padding': '10px',
    'width': '70%',
    'boxShadow': '0px 4px 8px rgba(0,0,0,0.2)',
    'zIndex': 10

}

hiddenLabel = {**LabelStyle, 'display': 'none'}
hiddenDropdown = {**DropdownStyle, 'display': 'none'}
hiddenDropdownContain = {**DropdownContain, 'display': 'none'}
hiddenButton = {**ButtonStyle, 'display': 'none'}
hiddenDoneButton = {**DoneButtonStyle, 'display': 'none'}
hiddenCheckbox = {**CheckboxStyle, 'display': 'none'}

visibleLabel = {**LabelStyle, 'display': 'block'}
visibleDropdown = {**DropdownStyle, 'display': 'block'}
visibleDropdownContain = {**DropdownContain, 'display': 'block'}
visibleButton = {**ButtonStyle, 'display': 'block'}
visibleDoneButton = {**DoneButtonStyle, 'display': 'block'}
visibleCheckbox = {**CheckboxStyle, 'display': 'block'}

hiddenPlot = {'display': 'none', 'width': '0%', 'height': '0%', 'margin-top': '20px'}
visiblePlot = {'display': 'block', 'width': '100%', 'height': '100%', 'margin-top': '20px'}


'''     This is the HTML format for the Dash Webpage
_________________________________________________________'''
app.layout = html.Div([
    dcc.Store(id='hiddenNetworkWindow', data={'is_hidden': True}),
    dcc.Store(id='hiddenPlotWindow', data={'is_hidden': True}),
    html.Div([
        html.Div([                      # Network Selection
            html.Div(
                children=[
                    html.Label(
                        "Folder:", 
                        style=visibleLabel
                    ),
                    dcc.Dropdown(
                        id='folder-dropdown',
                        options=[{'label': folder.name, 'value': folder.name} for folder in ROOT_DIRECTORY.iterdir() if folder.is_dir()],
                        placeholder="Select a folder...",
                        style=visibleDropdown
                    )
                ],
                style=TinyBoxStyle
            ),
            html.Div(
                [
                    html.Label(
                        "Network:", 
                        style=visibleLabel
                    ),
                    html.Button(
                        "Select Networks...",
                        id="network-window-toggle",
                        n_clicks=0,
                        style=visibleButton
                    ),
                    html.Div(
                        id="network-window",
                        children=[
                            dcc.Checklist(
                                id='network-dropdown',
                                options=[], 
                                style={**visibleDropdown, 'maxHeight': '150px', 'overflowY': 'auto'}
                            ),
                            html.Button(
                                "Done",
                                id="network-done",
                                n_clicks=0,
                                style=visibleDoneButton
                            )
                        ],
                        style=hiddenCheckbox
                    ),
                ], 
                style={
                    'display': 'flex',       # Use flexbox for horizontal alignment
                    'alignItems': 'center',   # Center items vertically
                    'position': 'relative'    # Ensure absolute positioning of custom dropdown works
                }
            )
        ],
        style=visibleDropdownContain
        ),
        html.Div([
            html.Div(
                [                
                    html.Label(
                        "Component:", 
                        id='component-label', 
                        style=hiddenLabel
                    ),
                    dcc.Dropdown(
                        id='component-dropdown', 
                        placeholder="Select a component...", 
                        style=hiddenDropdown
                    )                
                ],
                style=TinyBoxStyle
                
            ),
            html.Div(
                [
                    html.Label(
                        "Attribute:", 
                        id='attribute-label', 
                        style=hiddenLabel
                    ),
                    dcc.Dropdown(
                        id='attribute-dropdown', 
                        placeholder="Select an attribute...", 
                        style=hiddenDropdown
                    )
                ],
                style=TinyBoxStyle
            )
            
        ], 
        style=visibleDropdownContain
        ),
        html.Div([                      
            html.Div(
                [  
                    html.Label(
                        "Data Type:", 
                        id='datatype-label', 
                        style=hiddenLabel
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
                        style=hiddenDropdown
                    )
                ],
                style=TinyBoxStyle
                
            ),
            html.Div(
                [  
                    html.Label(
                        "Select Key/s:", 
                        id='keyselect-label', 
                        style=hiddenLabel
                    ),
                    dcc.Dropdown(
                        id='keyselect-dropdown', 
                        placeholder="Select keys...", 
                        style=hiddenDropdown,
                        multi=True
                    )
                ],
                style=TinyBoxStyle
                
            )
        ],
        style=visibleDropdownContain
        ),
        

        html.Div([                      
            html.Div(
                [  
                    html.Label(
                        "Tabulate Network:", 
                        id='tableselect-label', 
                        style=hiddenLabel
                    ),
                    dcc.Dropdown(
                        id='tableselect-dropdown', 
                        placeholder="Select network...",
                        style=hiddenDropdown
                    )
                ],
                style=TinyBoxStyle
                
            ),
            html.Div(
                [
                    html.Label(
                        "Plot:", 
                        id='plotselect-label', 
                        style=hiddenLabel
                    ),
                    html.Button(
                        "Select Networks to Plot...",
                        id="plot-window-toggle",
                        n_clicks=0,
                        style=hiddenButton
                    ),
                    html.Div(
                        id="plot-window",
                        children=[
                            dcc.Checklist(
                                id='plotselect-dropdown',
                                options=[], 
                                style={**visibleDropdown, 'maxHeight': '150px', 'overflowY': 'auto'}
                            ),
                            html.Button(
                                "Done",
                                id="plot-done",
                                n_clicks=0,
                                style=visibleDoneButton
                            )
                        ],
                        style=hiddenCheckbox
                    )                    
                ],
                style={
                    'display': 'flex',       # Use flexbox for horizontal alignment
                    'alignItems': 'center',   # Center items vertically
                    'position': 'relative'    # Ensure absolute positioning of custom dropdown works
                }
                
                
            )
        ],
        style=visibleDropdownContain
        ),       
    ],
    style=BigBoxStyle
    ),

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

network_data = NetworkData()



'''     Adds a list of Networks based on the Selected Folder
_________________________________________________________________'''
@app.callback(
    [
        Output('network-dropdown', 'options'),
        Output('plotselect-dropdown', 'options')
    ],
    [
        Input('folder-dropdown', 'value')
    ]    
)
def update_network_dropdown(selected_folder):
    if selected_folder is None:
        return [], []
    network_folder = ROOT_DIRECTORY / selected_folder
    network_files = [f.name for f in network_folder.iterdir() if f.suffix == '.h5']
    dropdown_options = [{'label': net, 'value': net} for net in network_files]
    return dropdown_options, dropdown_options


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
    [
        Output('component-dropdown', 'options'),
        Output('tableselect-dropdown', 'options'),
        Output('component-dropdown', 'style'), 
        Output('component-label', 'style'),
        Output('datatype-dropdown', 'style'),
        Output('datatype-label', 'style'),        
        Output('tableselect-dropdown', 'style'),
        Output('tableselect-label', 'style'),
        Output('network-done', 'n_clicks')
    ],
    [
        Input('network-done', 'n_clicks')
    ],
    [
        State('network-dropdown', 'value'),
        State('folder-dropdown', 'value')
    ]
)
def load_selected_network(doneClick, network_filenames, network_foldername):
    if doneClick and network_filenames:
        commonComponents = None
        finalNetworkList = []
        
        for selectedNetwork in network_filenames:
            if selectedNetwork not in network_data.networks:
                network_data.load_network(network_foldername, selectedNetwork)
            eachNetwork = network_data.get_network(selectedNetwork)
            if eachNetwork:
                currentComponents = set(eachNetwork.components.keys())
                if commonComponents is None:
                    commonComponents = currentComponents
                else:
                    commonComponents = commonComponents.intersection(currentComponents)
                finalNetworkList.append({'label': selectedNetwork, 'value': selectedNetwork})
                if not commonComponents:
                    break

        finalComponentList = [{'label': comp, 'value': comp} for comp in commonComponents] if commonComponents else []

        return (            
            finalComponentList,
            finalNetworkList,
            visibleDropdown, visibleLabel, 
            visibleDropdown, visibleLabel,
            visibleDropdown, visibleLabel,
            0
        )

    return (
        [], [],
        hiddenDropdown, hiddenLabel,
        hiddenDropdown, hiddenLabel,
        hiddenDropdown, hiddenLabel,
        0
    )






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
    [
        Output('data-output', 'children'),
        Output('data-graph', 'figure'),
        Output('attribute-dropdown', 'options'),
        Output('tableselect-dropdown', 'value'),
        Output('plotselect-dropdown', 'value'),
        Output('plot-done', 'n_clicks'),
        Output('data-output', 'style'), 
        Output('data-graph', 'style'),
        Output('attribute-dropdown', 'style'), 
        Output('attribute-label', 'style'),       
        Output('plot-window-toggle', 'style'),
        Output('plotselect-label', 'style')
    ],
    [       
        Input('component-dropdown', 'value'), 
        Input('datatype-dropdown', 'value'), 
        Input('attribute-dropdown', 'value'),
        Input('tableselect-dropdown', 'value'),
        Input('plot-done', 'n_clicks')
    ],
    [
        State('attribute-dropdown', 'options'),
        State('folder-dropdown', 'value'),
        State('tableselect-dropdown', 'value'),
        State('plotselect-dropdown', 'value'),
        State('data-output', 'style'), 
        State('data-graph', 'style'),
        State('attribute-dropdown', 'style'), 
        State('attribute-label', 'style'),
        State('plot-window-toggle', 'style'),
        State('plotselect-label', 'style'),
        State('network-dropdown', 'value')
    ]
)
def display_data(
        selectedComponent, dataType, selectedAttribute, 
        tabulateNetwork, doneClick, 
        currentAttribute, selectedFolder,
        currentTableNetwork, currentPlotNetwork,
        tableVis, plotVis,
        attrDropdownVis, attrLabelVis,
        plotWindowVisBtn, plotLabelVis,
        allNetworks
    ):    
    empty_fig = go.Figure(layout={"title": "No Data Available"})
    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Default output values
    output_content = html.Div("No data available.")
    fig = empty_fig
    attributeOptions = currentAttribute or []
    tableValue = currentTableNetwork
    plotValue = []
    if currentPlotNetwork:
        for plots in currentPlotNetwork:
            plotValue.append(plots)
    networkNames = ""
    commonAttributes = None
    
    # Maintain current visibility settings
    showOutput = tableVis
    showPlot = plotVis
    showAttrDropdown = attrDropdownVis
    showAttrLabel = attrLabelVis
    showPlotWindowBtn = plotWindowVisBtn
    showPlotLabel = plotLabelVis
    if dataType == "varying":
        showAttrDropdown = visibleDropdown
        showAttrLabel = visibleLabel

    if selectedComponent and selectedFolder:
        if dataType == "varying":
            for allNets in allNetworks:
                
                eachNetwork = network_data.get_network(allNets)
                if eachNetwork:
                    # Get varying attributes for the selected component in the current network
                    currentAttributes = network_data.get_varying_attributes(allNets, selectedComponent)
                    
                    if currentAttributes is not None:
                        if commonAttributes is None:
                            # Initialize commonAttributes with the first network's attributes
                            commonAttributes = set(currentAttributes)
                        else:
                            # Take the intersection of attributes
                            commonAttributes = commonAttributes.intersection(currentAttributes)

            # Convert common attributes to dropdown options
            attributeOptions = [{'label': attr, 'value': attr} for attr in commonAttributes] if commonAttributes else []

        if tabulateNetwork and not button_id == "plot-done":
            network_data.load_network(selectedFolder, tabulateNetwork)
            current_network = network_data.get_network(tabulateNetwork)
            
            if current_network is None:
                output_content = html.Div("No data available for the selected network.")
                return output_content, fig, attributeOptions, tableValue, plotValue, 0, showOutput, showPlot, showAttrDropdown, showAttrLabel, showPlotWindowBtn, showPlotLabel
            
            tableValue = tabulateNetwork
            showOutput = visible
            showPlot = hiddenPlot
            
            if dataType == "static":
                showAttrDropdown = hiddenDropdown
                showAttrLabel = hiddenLabel
                staticComponentData = network_data.get_all_static_data(tabulateNetwork, selectedComponent)
                if staticComponentData is not None:
                    output_content = dash_table.DataTable(
                        data=staticComponentData.to_dict('records'),
                        columns=[{"name": i, "id": i} for i in staticComponentData.columns],
                        page_size=10,
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left'},
                        style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'}
                    )
                else:
                    output_content = html.Div(f"No static data available for {tabulateNetwork} / {selectedComponent}.")
            
            elif dataType == "varying":         
                showPlotLabel = visibleLabel
                showPlotWindowBtn = visibleButton            
                output_content = html.Div("Select an attribute to view varying data.")
                
                if selectedAttribute:                    
                    varyingComponentData = network_data.get_varying_data(tabulateNetwork, selectedComponent, selectedAttribute)
                    if varyingComponentData is not None:
                        output_content = dash_table.DataTable(
                            data=varyingComponentData.to_dict('records'),
                            columns=[{"name": i, "id": i} for i in varyingComponentData.columns],
                            page_size=10,
                            style_table={'overflowX': 'auto'},
                            style_cell={'textAlign': 'left'},
                            style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'}
                        )
        elif dataType == "varying" and selectedAttribute:            
            showPlotLabel = visibleLabel
            showPlotWindowBtn = visibleButton
            if button_id == "plot-done" and len(plotValue) > 0:
                tableValue = None
                showPlot = visiblePlot
                showOutput = hidden
                for network in plotValue:
                    network_data.load_network(selectedFolder, network)
                    varyingComponentData = network_data.get_varying_data(network, selectedComponent, selectedAttribute)
                    if networkNames:
                        networkNames += f", '{network}'"
                    else:
                        networkNames += f"'{network}'"
                                        
                    if varyingComponentData is not None:                        
                        x_axis_data = varyingComponentData.iloc[:, 0]
                        y_columns = varyingComponentData.columns[1:]
                        for column in y_columns:
                            fig.add_trace(go.Scatter(
                                x=x_axis_data,
                                y=varyingComponentData[column],
                                mode='lines',
                                name=f"{column} ({network})"
                            ))
                    else:
                        showOutput = visible
                        output_content = html.Div("Error plotting. Network is empty.")
                fig.update_layout(title={"text": f"Comparing Attribute: ['{selectedAttribute}'] for Network/s: [{networkNames}]"})

    return (
        output_content, fig, attributeOptions, tableValue, plotValue, 0,
        showOutput, showPlot, showAttrDropdown, showAttrLabel, showPlotWindowBtn, showPlotLabel
    )



'''     Shows or Hides Multiple Dropdowns when the Data Type Dropdown is Changed
_________________________________________________________________________________________________________________'''


@app.callback(
    [
        Output("hiddenNetworkWindow", "data"),
        Output("hiddenPlotWindow", "data")
    ],
    [
        Input("network-window-toggle", "n_clicks"),
        Input("network-done", "n_clicks"),

        Input("plot-window-toggle", "n_clicks"),
        Input("plot-done", "n_clicks")
    ],
    [
        State("hiddenNetworkWindow", "data"),
        State("hiddenPlotWindow", "data")
    ], prevent_initial_call=True
)
def toggle_network_dropdown(toggleNetwork, doneNetwork, togglePlot, donePlot, network_window, plot_window):
    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "network-window-toggle":
        network_window['is_hidden'] = not network_window['is_hidden']
    elif button_id == "network-done":
        network_window['is_hidden'] = True
    if button_id == "plot-window-toggle":
        plot_window['is_hidden'] = not plot_window['is_hidden']
    elif button_id == "plot-done":
        plot_window['is_hidden'] = True

    return network_window, plot_window

@app.callback(
    Output("network-window", "style"),
    Input("hiddenNetworkWindow", "data")
)
def update_network_window_visibility(hidden_state):
    return hiddenCheckbox if hidden_state['is_hidden'] else visibleCheckbox

@app.callback(
    Output("plot-window", "style"),
    Input("hiddenPlotWindow", "data")
)
def update_plot_window_visibility(hidden_state):
    return hiddenCheckbox if hidden_state['is_hidden'] else visibleCheckbox

    



if __name__ == '__main__':
    app.run_server(debug=True)
