#/usr/bin/python3
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--CURAPACS_CUSTOMER", help="e.g. c0100 or c0566", type=str, required=True)
parser.add_argument("--CURAPACS_DOMAIN", help="e.g. curapacs.ch", type=str, required=False, default="curapacs.ch")
parser.add_argument("--CURAPACS_CLOUD_DICOM_AET", help="AET of orthanc in cloud", type=str, required=False, default="CURAPACS")
args = parser.parse_args()

parameters = { "CURAPACS_CUSTOMER": args.CURAPACS_CUSTOMER,
               "CURAPACS_DOMAIN": args.CURAPACS_DOMAIN }

with open(0) as stdin:
    for line in stdin:
        for parameter in parameters:
            line = line.replace(parameter, parameters[parameter])
        print(line, end='')
