
# Dicom-File-Format

# Dicom-Meta-Information-Header
# Used TransferSyntax: Little Endian Explicit
(0002,0000) UL 200                                      #   4, 1 FileMetaInformationGroupLength
(0002,0001) OB 00\01                                    #   2, 1 FileMetaInformationVersion
(0002,0002) UI [1.2.276.0.7230010.3.1.0.1]              #  26, 1 MediaStorageSOPClassUID
(0002,0003) UI [1.2.276.0.7230010.3.1.4.8323328.131065.1587929664.399909] #  56, 1 MediaStorageSOPInstanceUID
(0002,0010) UI =LittleEndianExplicit                    #  20, 1 TransferSyntaxUID
(0002,0012) UI [1.2.276.0.7230010.3.0.3.6.4]            #  28, 1 ImplementationClassUID
(0002,0013) SH [OFFIS_DCMTK_364]                        #  16, 1 ImplementationVersionName

# Dicom-Data-Set
# Used TransferSyntax: Little Endian Explicit
(0008,0050) SH [80372376]                               #   8, 1 AccessionNumber
(0010,0010) PN [Patient B]                              #  10, 1 PatientName
(0010,0020) LO [11788770005213]                         #  14, 1 PatientID
(0020,000d) UI [1.2.276.0.7230010.3.1.2.8323328.135028.1588014697.167604] #  56, 1 StudyInstanceUID
(0040,0100) SQ (Sequence with explicit length #=1)      # 162, 1 ScheduledProcedureStepSequence
  (fffe,e000) na (Item with explicit length #=7)          # 154, 1 Item
    (0008,0060) CS [US]                                     #   2, 1 Modality
    (0040,0001) AE [PhillipsUS01]                           #  12, 1 ScheduledStationAETitle
    (0040,0002) DA [20200427]                               #   8, 1 ScheduledProcedureStepStartDate
    (0040,0003) TM [100000.001]                             #  10, 1 ScheduledProcedureStepStartTime
    (0040,0006) PN [Max Messermann]                         #  14, 1 ScheduledPerformingPhysicianName
    (0040,0007) LO [try not to melt this patients brain for once] #  44, 1 ScheduledProcedureStepDescription
    (0040,0009) SH [80871868]                               #   8, 1 ScheduledProcedureStepID
  (fffe,e00d) na (ItemDelimitationItem for re-encoding)   #   0, 0 ItemDelimitationItem
(fffe,e0dd) na (SequenceDelimitationItem for re-encod.) #   0, 0 SequenceDelimitationItem
(0040,1001) SH [91249028]                               #   8, 1 RequestedProcedureID
