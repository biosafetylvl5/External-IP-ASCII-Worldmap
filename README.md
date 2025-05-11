# Network connectivity visualizer on an ASCII worldmap

A scalable tool to visually display your external IPs location via your CLI. Built on [f13rce/ConnectivityASCIIWorldmap](https://github.com/f13rce/ConnectivityASCIIWorldmap).

# Usage

After cloning, install the required packages:

``pip3 install -r requirements.txt --user``

Running the script:

``python3 showconnectivitymap.py``

# Comments

In this script there's a link to https://f13rce.net/ip.php to fetch the external IP address in case you were using a local IP. You can change this to any other web page. Copy over the ip.php file that only returns the page requester's IP to your web server and change the URL in the script.
