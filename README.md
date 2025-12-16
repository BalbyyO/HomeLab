# HomeLab
what not to do, at home

Installing Crowdsec

1. Install Crowdsec
To get the newest version, add the Crowdsec repository:
curl -s https://install.crowdsec.net | sudo sh

Update to refresh repo packages:
sudo apt update

Install Crowdsec package:
sudo apt install crowdsec

2. Install a Bouncer
Crowdsec won’t take action by default unless you install a bouncer to take care of things.
In our case, we want to ban IP addresses that attack our server.

Install firewall bouncer:
sudo apt install crowdsec-firewall-bouncer-iptables

Check what bouncers are active:
sudo cscli bouncers list

3. (optional) Change ports.
you may need to change this setting if you are running a service on port 8080.
sudo nano /etc/crowdsec/config.yaml
        api:
          server:
            listen_uri: 127.0.0.1:8080

Update local clients (IMPORTANT)
CrowdSec tools (cscli, bouncers) must know the new port.

sudo nano /etc/crowdsec/local_api_credentials.yaml

sudo nano /etc/crowdsec/bouncers/crowdsec-firewall-bouncer.yaml

everything needs to havet he new port number you assing

4. Turn on service
sudo pkill crowdsec
sudo systemctl restart crowdsec
sudo systemctl status crowdsec


5. enroll your server
make an account on (https://app.crowdsec.net)
sudo cscli console enroll 1234567890qwertyuiop

open the console and finish the enrollment on the website for the server you just linked 

6. working in progress...
