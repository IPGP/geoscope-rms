#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 12 12:59:55 2018

@author: leroy
"""

import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from obspy import UTCDateTime
from obspy import read, read_inventory
import sys
import os

from obspy.clients.filesystem.sds import Client


receivers = ['myaddress@mydomain.net']

smtp='mysmtpserver.mydomain.net'


end = UTCDateTime()
start = end-3600*24*30

loc_id_list = ["00","10"]
chan = "BH"
step = 3600

sds_path = "/SDS"
sds_client = Client(sds_path)


station_list = ["AIS","ATD","CAN","CCD","CLF","COYC","CRZF","DRV","DZM","ECH",
                "FDF","FOMA","FUTU","HDC","INU","IVI","KIP","MBO","MPG","NOUC",
                "PAF","PEL","PPTF","RER","ROCAM","SANVU","SPB","SSB","TAM",
                "TAOE","TRIS","UNM","WUS"]

t1 = start
t2 = start + step

ratios = {
        }
nz=[]
ez=[]
en=[]

n=[]
e=[]
z=[]

outer = MIMEMultipart()
me = 'geoscopegui@ipgp.fr'


# Add and image to the current email
####################################

def add_image(image_file):

    ctype, encoding = mimetypes.guess_type(image_file)
    if ctype is None or encoding is not None:
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)
    if maintype == 'text':
        fp = open(fichier)
        msg = MIMEText(fp.read(), _subtype=subtype)
        fp.close()
    elif maintype == 'image':
        fp = open(image_file, 'rb')
        msg = MIMEImage(fp.read(), _subtype=subtype)
        fp.close()
    else:
        fp = open(image_file, 'rb')
        msg = MIMEBase(maintype, subtype)
        msg.set_payload(fp.read())
        fp.close()
        encoders.encode_base64(msg)
    msg.add_header('Content-Disposition', 'attachment', filename=image_file)
    outer.attach(msg)
    os.remove(image_file)


## Format and send the final email
##################################

def send_mail():
    outer['Subject'] = 'RMS'
    outer['From'] = me

    composed = outer.as_string()

    s = smtplib.SMTP(smtp)
    for receiver in receivers:
        s.sendmail(me, receiver, composed)
    s.quit()




## Beginning
############

# Bandpass filter frequencies
freqmin = 0.1
freqmax = 0.5


# Loop over stations
for station_name in station_list:

	# Loop over locid
	for loc_id in loc_id_list:
	
		t1 = start
		t2 = start + step
		nz=[]
		ez=[]
		en=[]
		dates=[]

		fig, ax = plt.subplots()
		fig.suptitle(station_name + ' ' + loc_id + ' ' + chan + ' ' + start.strftime("%Y.%j") + "." + end.strftime("%Y.%j"), fontsize=20)
	
		while t1 < end :

			try :
				st = sds_client.get_waveforms(network='G', station=station_name, location=loc_id, channel=chan+"Z", starttime=t1, endtime=t2)
				tr=st[0]
				tr.filter('bandpass', freqmin=freqmin, freqmax=freqmax)
				z=tr.std()
		
				try : 
					st = sds_client.get_waveforms(network='G', station=station_name, location=loc_id, channel=chan+"N", starttime=t1, endtime=t2)
					tr=st[0]
					tr.filter('bandpass', freqmin=freqmin, freqmax=freqmax)
					n=tr.std()
		
					try : 
						st = sds_client.get_waveforms(network='G', station=station_name, location=loc_id, channel=chan+"E", starttime=t1, endtime=t2)
						tr=st[0]
						tr.filter('bandpass', freqmin=freqmin, freqmax=freqmax)
						e=tr.std()

						# If all std have been calculated (no exception)
						nz.append(n/z)
						ez.append(e/z)
						en.append(e/n)
			
						dates.append(t1)
					except:
						nz.append(0)
						ez.append(0)
						en.append(0)
				except:
					nz.append(0)
					ez.append(0)
					en.append(0)
			except:
				nz.append(0)
				ez.append(0)
				en.append(0)
		
			t1 = t2
			t2 = t2 + step

		ax.set_ylim(0, 3) 


		if all(val == 0 for val in nz) and all(val == 0 for val in en) and all(val == 0 for val in ez):
			print "All at 0"
		else :
			line, = ax.plot(nz, 'b,')
			line, = ax.plot(ez, 'r,')
			line, = ax.plot(en, 'g,')


			file_name = station_name + "." + start.strftime("%Y.%j") + "." + end.strftime("%Y.%j") + ".png"
			plt.savefig(file_name, bbox_inches='tight', dpi=72)
			add_image(file_name)
			plt.close()
    
else:
  send_mail()
  print("Finally finished!")

