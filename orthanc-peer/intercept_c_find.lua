function IncomingFindRequestFilter(source, origin)
   PrintRecursive(source)
   PrintRecursive(origin)
   json_source = DumpJson(source)
   RestApiPost('/enhancequery', json_source)
   return source
end
