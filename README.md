# Network connectivity visualizer on an ASCII worldmap

A scalable tool to visually display your external IPs location via your CLI. Built from [f13rce/ConnectivityASCIIWorldmap](https://github.com/f13rce/ConnectivityASCIIWorldmap).

# Usage

Install from GitHub:

``` bash
pip3 install --user git+https://github.com/biosafetylvl5/External-IP-ASCII-Worldmap.git
```

or after cloning, install the required packages:

``pip3 install . --user``

Run the script with `mapIP`.

# Comments

In this script there's a link to https://f13rce.net/ip.php to fetch the external IP address in case you were using a local IP. You can change this to any other web page. Copy over the ip.php file that only returns the page requester's IP to your web server and change the URL in the script.

The map used is not accurate to the real world. It is for display purposes, and does not attempt to make any statements beyond readability. Also sorry Antarctica, you didn't make the cut.
