import os
import tempfile
import datetime

import pydicom
from pydicom.dataset import Dataset, FileDataset, DataElement, datadict

json = {
  "PatientID": "11788770005213",
  "PatientName": "Patient B",
  "ScheduledProcedureStepSequence": [
    {
    "Modality": "US",
    "AETitle": "PhillipsUS01",
    "ProcedureStepStartDate": "20200427",
    "ProcedureStepStartTime": "100000",
    "PhysicianName": "Max Messermann"
  },
  {
    "Modality": "US",
    "AETitle": "PhillipsUS01",
    "ProcedureStepStartDate": "20200429",
    "ProcedureStepStartTime": "121650",
    "PhysicianName": "Max^Messermann"
  }]
}


# Create some temporary filenames
suffix = '.dcm'
filename_little_endian = "firstDicomFile"
filename_big_endian = "anotherDicomFile"

# creates the first dicom file
#filename_little_endian = tempfile.NamedTemporaryFile(suffix=suffix).name
# creates the second dicom file
#filename_big_endian = tempfile.NamedTemporaryFile(suffix=suffix).name

print("Setting file meta information...")
# Populate required values for file meta information
file_meta = Dataset()
file_meta.MediaStorageSOPClassUID = '1.2.276.0.7230010.3.1.0.1'
#file_meta.MediaStorageSOPInstanceUID = "1.2.3" # kill this
file_meta.ImplementationClassUID = "1.2.276.0.7230010.3.0.3.6.4" # kill this

print("Setting dataset values...")
# Create the FileDataset instance (initially no data elements, but file_meta
# supplied)
ds = FileDataset(filename_little_endian, {},
                 file_meta=file_meta, preamble=b"\0" * 128)

# Add the data elements -- not trying to set all required here. Check DICOM
# standard
ds.PatientName = json["PatientName"]
ds.PatientID = "123456"

a = Dataset()
a.Item = {}

a.Item.update({"Modality": "Philips"})
ds.ScheduledProcedureStepSequence = [a]
print(ds.to_json())

print(ds)
exit()


#ds.ScheduledProcedureStepSequence.append(json["ScheduledProcedureStepSequence"][0])


# Set the transfer syntax
ds.is_little_endian = True
ds.is_implicit_VR = True

# Set creation date/time
dt = datetime.datetime.now()
ds.ContentDate = dt.strftime('%Y%m%d')
timeStr = dt.strftime('%H%M%S.%f')  # long format with micro seconds
ds.ContentTime = timeStr

print("Writing test file", filename_little_endian)
ds.save_as(filename_little_endian)
print("File saved.")

# Write as a different transfer syntax XXX shouldn't need this but pydicom
# 0.9.5 bug not recognizing transfer syntax
ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRBigEndian
ds.is_little_endian = False
ds.is_implicit_VR = False

print("Writing test file as {} Explicit VR".format(filename_big_endian))
ds.save_as(filename_big_endian)

# reopen the data just for checking
for filename in (filename_little_endian, filename_big_endian):
    print('Load file {} ...'.format(filename))
    ds = pydicom.dcmread(filename)
    print(ds)

    # remove the created file
    print('Remove file {} ...'.format(filename))
    os.remove(filename)