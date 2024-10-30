________PyPSA Network Reader Shell________

_________About_________

This repository can help with any PyPSA network by viewing the data in tables and plots.

_______Functions_______

net_writer.py - (Writes a Webpage that can tabulate and plot any PyPSA Network)

network_run.ipynb - (runs net_writer.py on a localhost webpage and opens it)

_______How To Use_______

1   Copy files across into the main folder of the application that creates your network.

2   Open net_writer and make sure the imports work

3   Either move your *Network Files* into folder 'SavedNetworks' or rename the NETWORK_FOLDER in net_writer (line 25)

4   Once the networks are in the same folder: Open and Run network_run

5   You should be able to view the network either in your browser or in network_run

6   Restart your Kernel if the Network Folder has been modified (new networks or deleted networks)

*Requires networks to be saved as '.h5' files in the Network Folder*