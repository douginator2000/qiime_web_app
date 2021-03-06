#!/usr/bin/env python
# File created on 16 Feb 2011
from __future__ import division

__author__ = "Jesse Stombaugh"
__copyright__ = "Copyright 2010, The QIIME project"
__credits__ = ["Jesse Stombaugh", "Doug Wendel"]
__license__ = "GPL"
__version__ = "1.2.0-dev"
__maintainer__ = "Doug Wendel"
__email__ = "jesse.stombaugh@colorado.edu"
__status__ = "Development"


from optparse import make_option
from qiime.util import parse_command_line_parameters
from live_mgrast_rest_services import LiveMGRASTRestServices

script_info = {}
script_info['brief_description'] = "This script submits metadata to MG-RAST based on a study_id"
script_info['script_description'] = "This script takes a study_id and an MG-RAST web service key and performs metadata submission to the MG-RAST system."
script_info['script_usage'] = [("Example","This is an example usage", "python submit_data_to_mgrast.py -s 12345")]
script_info['output_description']= "There is no output from the script is puts the processed data into the Oracle DB."
script_info['required_options'] = [make_option('-s','--study_id', help='The study id to be exported')]
script_info['optional_options'] = [\
make_option('-d','--debug', action='store_true', help='Specifies that verbose debug output should be displayed.',default=False)
]
script_info['version'] = __version__

def main():
    option_parser, opts, args = parse_command_line_parameters(**script_info)

    # define the variables
    study_id = opts.study_id
    debug = opts.debug
    
    # User_ID. Mine for now for access to all studies.
    web_app_user_id = 12169
    
    # Get the live function reference
    live_rest_services = LiveMGRASTRestServices(study_id, web_app_user_id)
    
    # Send the metadata and sequence data
    result = live_rest_services.generate_metadata_files(debug, True)
        
if __name__ == "__main__":
    main()
