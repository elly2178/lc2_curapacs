#include <Plugins/Samples/Common/OrthancPluginCppWrapper.h>      
#include <Core/SystemToolbox.h>   
#include <Core/Toolbox.h>   
#include <Core/Logging.h>  
#include <json/value.h>
#include <json/reader.h>  
#include <string>  
#include <Plugins/Include/orthanc/OrthancCPlugin.h>

ORTHANC_PLUGINS_API OrthancPluginErrorCode OnFindCallback (OrthancPluginFindAnswers *answers,
     const OrthancPluginFindQuery *query, const char *issuerAet, const char *calledAet)
{
  OrthancPluginContext* context = OrthancPlugins::GetGlobalContext(); 
  OrthancPluginMemoryBuffer temp2;

  //std::string s = std::to_string(taggroup);
  //char const *pchar = s.c_str();
  /*
  OrthancPlugins::MemoryBuffer dicom;
  Json::Value json;
  dicom.GetDicomQuery((OrthancPluginWorklistQuery*) query);
  dicom.DicomToJson(json, OrthancPluginDicomToJsonFormat_Short, static_cast<OrthancPluginDicomToJsonFlags>(0), 0);
  char* post_body = OrthancPluginDicomBufferToJson(context,
                                                    query,
                                                    sizeof(query),
                                                    OrthancPluginDicomToJsonFormat_Full, 
                                                    OrthancPluginDicomToJsonFlags_IncludePrivateTags, 
                                                    0);
  
  OrthancPlugins::LogInfo("Received query from remote modality " +
                          std::string(issuerAet) + ":\n" + json.toStyledString());
  */
  
  std::string json_body = "{";

  for (uint16_t i = 0; i < OrthancPluginGetFindQuerySize(context, query); i++)
  {  
    uint16_t  taggroup, tagelement;
    uint16_t* taggroup_ptr = &taggroup;
    uint16_t* tagelement_ptr = &tagelement;
    OrthancPluginGetFindQueryTag(context, taggroup_ptr, tagelement_ptr, query, i);
    char* tagvalue = OrthancPluginGetFindQueryValue(context, query, i);

    std::stringstream taggroup_str, tagelement_str;
    taggroup_str << std::setfill('0') << std::setw(4) << std::hex << taggroup;
    tagelement_str << std::setfill('0') << std::setw(4) << std::hex << tagelement;

    std::string json_tuple = "\"" + taggroup_str.str() + "," + tagelement_str.str() + "\"" + ":" 
                              + "\"" + tagvalue + "\"";
    if(i < OrthancPluginGetFindQuerySize(context, query)-1) {
      json_tuple = json_tuple + ", ";
    }
    json_body = json_body + json_tuple;
  }
  json_body = json_body + "}";
  


  OrthancPluginErrorCode enhanceError = OrthancPluginRestApiPostAfterPlugins(context, 
                                                                             &temp2,
                                                                             "/enhancequery",
                                                                             json_body.c_str(),
                                                                             strlen(json_body.c_str()));


  if (enhanceError) {
    return enhanceError;
  }

 char * sample_json_big = "[{\"00100021\":{\"vr\":\"LO\",\"Value\":[\"Hospital A\"]}}]";
 char * sample_json = "{}";

 //std::string string_data = (char*) temp2.data;
 std::string string_data = sample_json_big;
 //std::string string_data_cropped = string_data.substr(0,string_data.length());
 Json::Value root;
 Json::Reader reader;
 Json::FastWriter writer;

 bool parsedSuccess = reader.parse(string_data, root, false);
 if(not parsedSuccess)
 {
   OrthancPluginLogWarning(context, "Failed to parse JSON");
   return OrthancPluginErrorCode_BadJson;
 }

    Json::FastWriter writer;
    std::string s = writer.write(root[0]);


  OrthancPluginLogWarning(context, "Iterating over json structure now: ");
  OrthancPluginLogWarning(context, root[0].toStyledString().c_str());
  OrthancPluginLogWarning(context, "##############################################");
  OrthancPluginMemoryBuffer dicom_buffer2;
  OrthancPluginErrorCode dicom_return_code2 = OrthancPluginCreateDicom(context, &dicom_buffer2,
                                                 root[0].toStyledString().c_str(), NULL, OrthancPluginCreateDicomFlags_DecodeDataUriScheme);
  if (dicom_return_code2) {
      OrthancPluginLogWarning(context, "Failed to convert json to DICOM");
    }
    OrthancPluginLogWarning(context, "##############################################");

    OrthancPluginFindAddAnswer(context, answers, &dicom_buffer2.data, root[0].size());

  OrthancPluginFreeMemoryBuffer(context, &dicom_buffer2);
  OrthancPluginLogWarning(context, "##############################################");

/*
  for(unsigned int index=0; index<(uint) root.size(); ++index) {
    std::string tags_string = writer.write(root[index]);
    OrthancPluginLogWarning(context, tags_string.c_str());
    OrthancPluginMemoryBuffer dicom_buffer;
    OrthancPluginErrorCode dicom_return_code = OrthancPluginCreateDicom(context, &dicom_buffer,
                                                 tags_string.c_str(), NULL, OrthancPluginCreateDicomFlags_None);
    if (dicom_return_code) {
      OrthancPluginLogWarning(context, "Failed to convert json to DICOM");
    }
    OrthancPluginFindAddAnswer(context, answers, &dicom_buffer.data, dicom_buffer.size);
  }
*/

  OrthancPluginFreeMemoryBuffer(context, &temp2);
  return OrthancPluginErrorCode_Success;


}

extern "C"
{    
  ORTHANC_PLUGINS_API int32_t OrthancPluginInitialize(OrthancPluginContext* context)     
  {    
    Orthanc::Logging::Initialize(context);    
    OrthancPlugins::SetGlobalContext(context);   
    OrthancPluginSetDescription(context, "Orthanc Plugin Enhance Incoming C-Find queries");
    OrthancPluginRegisterFindCallback(context, (OrthancPluginFindCallback) OnFindCallback);
    return 0;   
  }    
  ORTHANC_PLUGINS_API void OrthancPluginFinalize()    
  {   
    LOG(INFO) << "NanoPlugin is finalizing";   
  }    
  ORTHANC_PLUGINS_API const char* OrthancPluginGetName()    
  {    
    return "NanoPlugin";    
  }     
  ORTHANC_PLUGINS_API const char* OrthancPluginGetVersion()    
  {    
    return "1.0.0";    
  }    
} 
