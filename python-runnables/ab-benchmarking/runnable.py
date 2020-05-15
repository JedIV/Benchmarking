# This file is the actual code for the Python runnable ab-benchmarking
from dataiku.runnables import Runnable
from dataiku.customrecipe import *

class MyRunnable(Runnable):
    """The base interface for a Python runnable"""

    def __init__(self, project_key, config, plugin_config):
        """
        :param project_key: the project in which the runnable executes
        :param config: the dict of the configuration of the object
        :param plugin_config: contains the plugin settings
        """
        self.project_key = project_key
        self.config = config
        self.plugin_config = plugin_config
        
    def get_progress_target(self):
        """
        If the runnable will return some progress info, have this function return a tuple of 
        (target, unit) where unit is one of: SIZE, FILES, RECORDS, NONE
        """
        return None

    def run(self, progress_callback):
        # -*- coding: utf-8 -*-
        import json
        import io
        import os
        import subprocess
        import pandas as pd
        import matplotlib

        # Prerequisites: apache bench installed on your machine


        # Required variables

        url            = self.config.get('url'           )
        service        = self.config.get('service'       )
        endpoint       = self.config.get('endpoint'      )
        endpoint_type  = self.config.get('endpoint_type' )
        post_variables = self.config.get('post_variables')
        num_requests   = self.config.get('num_requests'  )
        concurrency    = self.config.get('concurrency'   )
        api_key        = self.config.get('api_key'       )

        ## endpoint types:
        endpoints = {"prediction"     : "predict", 
                     "code"           : "run"    , 
                     "sql_query"      : "query"  , 
                     "dataset_lookup" : "lookup" }

        # Make it work for Python 2+3 and with Unicode
        try:
            to_unicode = unicode
        except NameError:
            to_unicode = str

        # Define data
        data = json.loads(post_variables)
        
        # Write JSON file
        with open('data.json', 'w') as outfile:  
            json.dump(data, outfile)
        # Write JSON file
        #with io.open('/Users/jediv/data.json', 'w', encoding='utf8') as outfile:
        #    data = json.dumps(data, ensure_ascii=False, encoding='utf8')
        #    outfile.write(unicode(data))
        #    print data

        # Build request URL    
        req_url = url + "/public/api/v1/" + service + "/" + endpoint + "/" + endpoints[endpoint_type]
        
        # Build AB call
        if not api_key:
            ab_call = "ab -l -e output.csv -n " + str(num_requests) + " -c " + str(concurrency) + " -p " + "data.json -T application/json " + req_url
            
            # More pythonic?
            # ab_call = "ab -l -e output.csv -n %s  -c  %s -p  %s /data.json -T application/json %s" % (str(num_requests), str(concurrency), os.getcwd(), req_url)
        else:
            ab_call = "ab -l -e output.csv -A " + api_key + ": -n " + str(num_requests) + " -c " + str(concurrency) + " -p " + os.getcwd() + "/data.json -T application/json " + req_url 
        
        # Make call and get text output of Apache Bench Call
        text_output = subprocess.check_output(ab_call, shell=True)
        
        # Generate plot and save it
        results = pd.read_csv(os.getcwd() + "/output.csv")
        scat  = results.plot.scatter('Percentage served', 'Time in ms')        
        fig = scat.get_figure()
        fig.savefig(os.getcwd() + 'figure.png')
        
        # Turn plot into html
        data_uri = open(os.getcwd() + 'figure.png', 'rb').read().encode('base64').replace('\n', '')
        img_tag = '<img src="data:image/png;base64,{0}">'.format(data_uri)
        
        # Return HTML
        return "<pre> APACHE BENCH CALL: \n" + ab_call + "\n </pre>"+ "<pre>" + text_output + "</pre>" + img_tag
        