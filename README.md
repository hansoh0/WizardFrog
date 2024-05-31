
# rTwo

rTwo is the not-so state-of-the-art discord bot featuring randomized gifs and pictures, role management, automated announcements, a suggestion box, and jukebox functionality @hansoh0 (https://www.github.com/hansoh0)

## Installation

Install requirements with pip

```
pip install -r requirements.txt
```
## How to Use
The bot is best set up as a service on a container
```
sudo vi /etc/systemd/system/rtwo.service
```
```
[Unit]                                                                                                                                                                                                     
Description=R2 is the not so state-of-the-art discord bot                                                                                                                                                
After=networking.target                                                                                                                                                                                    
                                                                                                                                                                                                           
[Service]                                                                                                                                                                                                  
User=rtwo                                                                                                                                                                                                  
ExecStart=/usr/bin/python3 /home/rtwo/app/r2.py                                                                                                                                              
                                                                                                                                                                                                           
[Install]                                                                                                                                                                                                  
WantedBy=multi-user.target
```

