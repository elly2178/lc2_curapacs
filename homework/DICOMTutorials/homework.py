'''
1. curaPACS startet
// orthanc things: kubectl apply -f orthanc/manifeat.yml
4. (not so important) curaPACS-Test lässt sich erfolgreiche Speicherung durch Storage Commitment bestätigen

'''
# use subprocess to "convert" cmds to py3
from subprocess import Popen, PIPE
from sys import argv
import time

# for animation
import itertools
import threading
import sys

# for Finding Patients
from pydicom.dataset import Dataset
from pynetdicom import AE
from pynetdicom.sop_class import PatientRootQueryRetrieveInformationModelFind

# Connection
print("Verifying  DICOM connectivity: ")
utility="echoscu"

try:
    port= argv[2]
except IndexError:
    port = "4242"

try:
    hostname = argv[1]
except IndexError:
    hostname = "c0100-orthanc.curapacs.ch"

cmd = " ".join([utility,hostname,port])

# gets the current time that is takes for the pc to get a response from the curapacs
startTime = time.perf_counter()

p = Popen(cmd , shell=True, stdout=PIPE, stderr=PIPE)
out, err = p.communicate()
endTime = time.perf_counter()
if p.returncode == 0:
    print("You have successfully accessed the Hostname: " + hostname)
    print("Time elapsed to access target: ", round(endTime - startTime,3)," seconds")
else:
    print("Unable ot access Hostname " + hostname + "\nPlease check the Hostname spelling or the Port number")
    # in case of error, exit program 
    exit(1)

print("--"*40)
#  curaPACS-Test versucht DICOM C-Store mit verschiedenen Testdatensätzen
print("Transmitting DICOM Images: ")
exe = "storescu"
directories = "--scan-directories"
# host & port ==
pathRow = "/home/schumi/lc2/testdaten/PATIENT_H"
#pathUltimate = "PATIENT_B"
cmd2 = " ".join([exe,directories, hostname, port, pathRow])
print(cmd2)


# animation
done = False
def animate():
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if done:
            break
        sys.stdout.write('\rloading ' + c)
        sys.stdout.flush()
        time.sleep(0.1)
    
# Log Zeiten und Resultat
startTimePush = time.perf_counter()
 

q = Popen(cmd2 , shell=True, stdout=PIPE, stderr=PIPE)
out, err = q.communicate()
endTimePush = time.perf_counter()
t = threading.Thread(target=animate)
t.start()

#long process here -- 4 animation :)
time.sleep(4)
done = True

if q.returncode == 0:
    print("\nPushing Images")
    cmd2 = " ".join([exe,directories, hostname, port, pathRow])
    
    print("Images has been successfully pushed")
    
else:
    videoErr = "--propose-lossless"
    cmd2 = " ".join([exe, videoErr, directories, hostname, port, pathRow])
    print("\nVideo has been pushed")

print("Time elapsed: ", round(endTimePush - startTimePush,4))
print("--"*40)

 # Finding Patients
print("Finding Patient: ")
 # Initialise the Application Entity
ae = AE(ae_title='FINDSCU')

# animation
animate()

# Log Zeiten und Resultat
startTimeFind = time.perf_counter()

# Add a requested presentation context
ae.add_requested_context(PatientRootQueryRetrieveInformationModelFind)

# Create our Identifier (query) dataset
ds = Dataset()
ds.PatientName = 'P*'
ds.PatientID = "11788*"
ds.QueryRetrieveLevel = 'STUDY'

# Associate with peer AE at IP 127.0.0.1 and port 11112
assoc = ae.associate(hostname, int(port))

if assoc.is_established:
    # Use the C-FIND service to send the identifier
    responses = assoc.send_c_find(ds, PatientRootQueryRetrieveInformationModelFind)
    for (status, identifier) in responses:
        if status:
            print('C-FIND query status: 0x{0:04x}'.format(status.Status))

            # If the status is 'Pending' then identifier is the C-FIND response
            if status.Status in (0xFF00, 0xFF01):
                print(identifier)
        else:
            print('Connection timed out, was aborted or received invalid response')

     # Release the association
    assoc.release()
else:
    print('Association rejected, aborted or never connected')

endTimeFind = time.perf_counter()
print("Time needed to Find the Patient: ", round(endTimeFind - startTimeFind,4))